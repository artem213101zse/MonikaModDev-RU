// Official DDLC zip lives behind the itch.io widget on ddlc.moe.
// Flow: csrf → /download_url → download page → /file/{id} → signed CDN URL.
package ru.kurokawa.mas.bios;

import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.CookieHandler;
import java.net.CookieManager;
import java.net.CookiePolicy;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLEncoder;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class DdlcItch {

    public static final String DEFAULT_ITCH = "https://teamsalvato.itch.io/ddlc";
    public static final String DEFAULT_UPLOAD = "DDLC (Windows)";

    private static final String UA =
            "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 "
                    + "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36";
    private static final Pattern CSRF =
            Pattern.compile("csrf_token\"\\s+value=\"([^\"]+)\"");
    private static final Pattern UPLOAD_ID =
            Pattern.compile("data-upload_id=\"(\\d+)\"");

    private DdlcItch() {
    }

    public static void ensureCookies() {
        if (CookieHandler.getDefault() != null) {
            return;
        }
        CookieManager mgr = new CookieManager();
        mgr.setCookiePolicy(CookiePolicy.ACCEPT_ALL);
        CookieHandler.setDefault(mgr);
    }

    public static String resolveZipUrl(String itchGame, String uploadName) throws IOException {
        ensureCookies();
        itchGame = trimSlash(itchGame);
        if (itchGame.length() == 0) {
            itchGame = DEFAULT_ITCH;
        }
        if (uploadName == null || uploadName.length() == 0) {
            uploadName = DEFAULT_UPLOAD;
        }
        String purchase = itchGame + "/purchase";
        String html = httpGet(purchase, itchGame);
        String csrf = findCsrf(html);
        if (csrf == null) {
            throw new IOException("нет csrf на itch.io");
        }
        String json = httpPost(
                itchGame + "/download_url",
                "csrf_token=" + URLEncoder.encode(csrf, "UTF-8"),
                purchase);
        JSONObject obj = parseJson(json);
        if (obj.has("errors")) {
            throw new IOException("itch download_url: " + obj.opt("errors"));
        }
        String dlPage = obj.optString("url", "");
        if (dlPage.length() == 0) {
            throw new IOException("itch не дал страницу загрузки");
        }
        String page = httpGet(dlPage, purchase);
        String csrf2 = findCsrf(page);
        if (csrf2 != null) {
            csrf = csrf2;
        }
        String uploadId = findUploadId(page, uploadName);
        if (uploadId == null) {
            throw new IOException("на странице нет файла " + uploadName);
        }
        json = httpPost(
                itchGame + "/file/" + uploadId,
                "csrf_token=" + URLEncoder.encode(csrf, "UTF-8"),
                dlPage);
        obj = parseJson(json);
        if (obj.has("errors")) {
            throw new IOException("itch file: " + obj.opt("errors"));
        }
        String zipUrl = obj.optString("url", "");
        if (zipUrl.length() == 0) {
            throw new IOException("itch не дал ссылку на zip");
        }
        return zipUrl;
    }

    public static boolean urlLooksLikeZip(String url) {
        if (url == null || url.length() == 0) {
            return false;
        }
        HttpURLConnection conn = null;
        try {
            conn = open(url, "HEAD", null);
            int code = conn.getResponseCode();
            if (code >= 400) {
                return false;
            }
            String type = conn.getContentType();
            if (type != null && type.toLowerCase().indexOf("html") >= 0) {
                return false;
            }
            long len = contentLength(conn);
            if (type != null) {
                String lower = type.toLowerCase();
                if (lower.indexOf("zip") >= 0 || lower.indexOf("octet-stream") >= 0) {
                    return len <= 0 || len > 1024 * 1024;
                }
            }
            if (len > 50L * 1024L * 1024L) {
                return true;
            }
        } catch (Exception e) {
            return false;
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
        return false;
    }

    private static String findCsrf(String html) {
        if (html == null) {
            return null;
        }
        Matcher m = CSRF.matcher(html);
        if (m.find()) {
            return m.group(1);
        }
        return null;
    }

    private static String findUploadId(String html, String uploadName) {
        if (html == null) {
            return null;
        }
        String needle = uploadName.toLowerCase();
        Matcher named = Pattern.compile(
                "data-upload_id=\"(\\d+)\"[\\s\\S]{0,900}?" + Pattern.quote(uploadName),
                Pattern.CASE_INSENSITIVE).matcher(html);
        if (named.find()) {
            return named.group(1);
        }
        Matcher any = UPLOAD_ID.matcher(html);
        String first = null;
        while (any.find()) {
            if (first == null) {
                first = any.group(1);
            }
            int from = any.start();
            int to = Math.min(html.length(), from + 900);
            if (html.substring(from, to).toLowerCase().indexOf(needle) >= 0) {
                return any.group(1);
            }
        }
        return first;
    }

    private static JSONObject parseJson(String raw) throws IOException {
        if (raw == null || raw.length() == 0) {
            throw new IOException("пустой ответ itch.io");
        }
        try {
            return new JSONObject(raw);
        } catch (Exception e) {
            throw new IOException("не JSON от itch.io");
        }
    }

    private static String httpGet(String url, String referer) throws IOException {
        HttpURLConnection conn = null;
        try {
            conn = open(url, "GET", referer);
            return readBody(conn);
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }

    private static String httpPost(String url, String body, String referer) throws IOException {
        HttpURLConnection conn = null;
        try {
            conn = open(url, "POST", referer);
            conn.setDoOutput(true);
            conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
            conn.setRequestProperty("Accept", "application/json, text/javascript, */*; q=0.01");
            conn.setRequestProperty("X-Requested-With", "XMLHttpRequest");
            OutputStream out = conn.getOutputStream();
            try {
                out.write(body.getBytes("UTF-8"));
                out.flush();
            } finally {
                out.close();
            }
            return readBody(conn);
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }

    private static HttpURLConnection open(String url, String method, String referer) throws IOException {
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setInstanceFollowRedirects(true);
        conn.setConnectTimeout(20000);
        conn.setReadTimeout(30000);
        conn.setRequestMethod(method);
        conn.setRequestProperty("User-Agent", UA);
        conn.setRequestProperty("Accept", "text/html,application/json,application/xhtml+xml,*/*");
        if (referer != null && referer.length() > 0) {
            conn.setRequestProperty("Referer", referer);
            conn.setRequestProperty("Origin", "https://teamsalvato.itch.io");
        }
        return conn;
    }

    private static String readBody(HttpURLConnection conn) throws IOException {
        int code = conn.getResponseCode();
        InputStream in = code >= 400 ? conn.getErrorStream() : conn.getInputStream();
        if (in == null) {
            throw new IOException("HTTP " + code);
        }
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buf = new byte[8192];
        int n;
        while ((n = in.read(buf)) >= 0) {
            if (n > 0) {
                out.write(buf, 0, n);
            }
        }
        in.close();
        String text = out.toString("UTF-8");
        if (code >= 400) {
            throw new IOException("HTTP " + code);
        }
        return text;
    }

    private static long contentLength(HttpURLConnection conn) {
        try {
            String raw = conn.getHeaderField("Content-Length");
            if (raw == null || raw.length() == 0) {
                return -1L;
            }
            return Long.parseLong(raw.trim());
        } catch (Exception e) {
            return -1L;
        }
    }

    private static String trimSlash(String url) {
        if (url == null) {
            return "";
        }
        String out = url.trim();
        while (out.endsWith("/")) {
            out = out.substring(0, out.length() - 1);
        }
        return out;
    }
}
