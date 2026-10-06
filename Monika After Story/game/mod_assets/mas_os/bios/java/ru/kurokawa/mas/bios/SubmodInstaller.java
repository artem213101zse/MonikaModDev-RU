// Installs a submod zip into Documents/.../game with backups for uninstall.
package ru.kurokawa.mas.bios;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Enumeration;
import java.util.List;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

public class SubmodInstaller {

    public static class Result {
        public boolean ok;
        public String message = "";
        public String id = "";
        public int added;
        public int replaced;
        public int skipped;
    }

    public static File masDir(File sideload) {
        return new File(sideload, "_mas");
    }

    public static File submodsRoot(File sideload) {
        return new File(masDir(sideload), "submods");
    }

    public static File manifestDir(File sideload) {
        return new File(submodsRoot(sideload), "installed");
    }

    public static File backupRoot(File sideload) {
        return new File(submodsRoot(sideload), "backups");
    }

    public static File vanillaRoot(File sideload) {
        return new File(submodsRoot(sideload), "vanilla");
    }

    public static File payloadRoot(File sideload) {
        return new File(submodsRoot(sideload), "payloads");
    }

    private static File vanillaFile(File sideload, Dest dest) {
        return new File(vanillaRoot(sideload), dest.root + "/" + dest.rel);
    }

    private static File payloadFile(File sideload, String id, Dest dest) {
        return new File(new File(payloadRoot(sideload), id), dest.root + "/" + dest.rel);
    }

    public static Result install(File zip, File gameOverlay, File sideload) {
        Result result = new Result();
        if (zip == null || !zip.isFile()) {
            result.message = "Нет zip сабмода.";
            return result;
        }
        if (gameOverlay == null || sideload == null) {
            result.message = "Нет папки Documents/game.";
            return result;
        }
        if (!gameOverlay.isDirectory() && !gameOverlay.mkdirs()) {
            result.message = "Не создалась game для сабмода.";
            return result;
        }
        ZipFile zipFile = null;
        try {
            zipFile = new ZipFile(zip);
            List<String> names = new ArrayList<String>();
            Enumeration<? extends ZipEntry> scan = zipFile.entries();
            while (scan.hasMoreElements()) {
                ZipEntry entry = scan.nextElement();
                if (entry == null || entry.isDirectory()) {
                    continue;
                }
                String raw = entry.getName();
                if (junkZipName(raw)) {
                    continue;
                }
                names.add(normalize(raw));
            }
            if (names.isEmpty()) {
                result.message = "В zip нет файлов.";
                return result;
            }
            String prefix = commonPrefix(names);
            String pack = packName(zip.getName(), prefix);
            result.id = safeId(pack);
            String guessed = classifyKind(names);
            boolean asSprite = "spritepack".equals(guessed);
            boolean asAsset = "assetpack".equals(guessed);
            File existingMan = new File(manifestDir(sideload), result.id + ".json");
            if (existingMan.isFile()) {
                uninstall(result.id, gameOverlay, sideload);
            }
            File backupDir = new File(backupRoot(sideload), result.id);
            File payloadDir = new File(payloadRoot(sideload), result.id);
            JSONArray added = new JSONArray();
            JSONArray replaced = new JSONArray();
            int count = 0;
            Enumeration<? extends ZipEntry> entries = zipFile.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (entry == null || entry.isDirectory()) {
                    continue;
                }
                String raw = entry.getName();
                if (junkZipName(raw)) {
                    result.skipped++;
                    continue;
                }
                String relative = peel(normalize(raw), prefix);
                Dest dest = destFor(relative, pack, asSprite, asAsset, gameOverlay);
                if (dest == null) {
                    result.skipped++;
                    continue;
                }
                File base = rootFor(dest, gameOverlay, sideload);
                File out = new File(base, dest.rel);
                if (!staysInside(base, out)) {
                    result.skipped++;
                    continue;
                }
                File parent = out.getParentFile();
                if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
                    result.skipped++;
                    continue;
                }
                if (out.isFile()) {
                    File vanilla = vanillaFile(sideload, dest);
                    File vanParent = vanilla.getParentFile();
                    if (vanParent != null && !vanParent.isDirectory()) {
                        vanParent.mkdirs();
                    }
                    // Snapshot only the original game file. If another submod
                    // already owns this path, vanilla stays the first snapshot.
                    if (!vanilla.isFile() && !otherOwnsKey(dest.key(), result.id, sideload)) {
                        copyFile(out, vanilla);
                    }
                    File bak = backupFile(backupDir, dest);
                    File bakParent = bak.getParentFile();
                    if (bakParent != null && !bakParent.isDirectory()) {
                        bakParent.mkdirs();
                    }
                    if (!bak.isFile()) {
                        copyFile(out, bak);
                    }
                    replaced.put(dest.key());
                    result.replaced++;
                } else {
                    added.put(dest.key());
                    result.added++;
                }
                copyEntry(zipFile, entry, out);
                File payload = payloadFile(sideload, result.id, dest);
                File payParent = payload.getParentFile();
                if (payParent != null && !payParent.isDirectory()) {
                    payParent.mkdirs();
                }
                copyFile(out, payload);
                count++;
            }
            if (count <= 0) {
                result.message = "Ни одного файла не поставилось. Zip не похож на сабмод.";
                return result;
            }
            JSONObject man = new JSONObject();
            man.put("id", result.id);
            man.put("name", zip.getName());
            man.put("pack", pack);
            man.put("added", added);
            man.put("replaced", replaced);
            man.put("files", count);
            man.put("installedAt", System.currentTimeMillis());
            String kind = asSprite ? "spritepack" : (asAsset ? "assetpack" : "submod");
            man.put("kind", kind);
            File manDir = manifestDir(sideload);
            if (!manDir.isDirectory() && !manDir.mkdirs()) {
                result.message = "Поставлено " + count + " файлов, но манифест не записался.";
                result.ok = true;
                return result;
            }
            writeText(new File(manDir, result.id + ".json"), man.toString());
            result.ok = true;
            String label = asSprite ? "Спрайтпак" : (asAsset ? "Рескин" : "Сабмод");
            String extra = asSprite
                    ? ". Подарки в characters, картинки в mod_assets/monika. Перезапусти MAS."
                    : (asAsset
                            ? ". Картинки подменились в игре (понга, доски и т.п.). Перезапусти MAS."
                            : ". Включить пак можно в MAS OS после запуска.");
            result.message = label + " «" + pack + "»: файлов " + count
                    + ", новых " + result.added
                    + ", заменено (бекап) " + result.replaced
                    + (result.skipped > 0 ? ", пропуск " + result.skipped : "")
                    + extra;
            return result;
        } catch (Exception e) {
            result.message = "Установка сабмода: " + e.getMessage();
            return result;
        } finally {
            if (zipFile != null) {
                try {
                    zipFile.close();
                } catch (Exception ignored) {
                }
            }
        }
    }

    public static Result uninstall(String id, File gameOverlay, File sideload) {
        Result result = new Result();
        if (id == null || id.length() == 0) {
            result.message = "Не выбран сабмод.";
            return result;
        }
        File manFile = new File(manifestDir(sideload), id + ".json");
        if (!manFile.isFile()) {
            result.message = "Манифеста нет: " + id;
            return result;
        }
        try {
            JSONObject man = new JSONObject(readText(manFile));
            JSONArray added = man.optJSONArray("added");
            JSONArray replaced = man.optJSONArray("replaced");
            File backupDir = new File(backupRoot(sideload), id);
            int restored = 0;
            int deleted = 0;
            JSONArray keys = new JSONArray();
            appendKeys(keys, added);
            appendKeys(keys, replaced);
            for (int i = 0; i < keys.length(); i++) {
                Dest dest = Dest.parse(keys.optString(i, ""));
                if (dest == null) {
                    continue;
                }
                int act = restoreLive(dest, id, gameOverlay, sideload);
                if (act > 0) {
                    restored++;
                } else if (act < 0) {
                    deleted++;
                }
            }
            dropOwnedTrees(keys, id, gameOverlay, sideload);
            String packLabel = man.optString("pack", id);
            if (packLabel != null && packLabel.length() > 0
                    && !otherOwnsPrefix("game:Submods/" + packLabel, id, sideload)) {
                deleteTree(new File(gameOverlay, "Submods/" + packLabel));
            }
            deleteTree(backupDir);
            deleteTree(new File(payloadRoot(sideload), id));
            manFile.delete();
            result.ok = true;
            result.id = id;
            String goneKind = man.optString("kind", "submod");
            String goneLabel = "spritepack".equals(goneKind)
                    ? "Спрайтпак"
                    : ("assetpack".equals(goneKind) ? "Рескин" : "Сабмод");
            result.message = goneLabel + " «" + packLabel + "» снят: удалено "
                    + deleted + ", возвращено " + restored + ".";
            return result;
        } catch (Exception e) {
            result.message = "Удаление: " + e.getMessage();
            return result;
        }
    }

    public static String listReport(File sideload) {
        File dir = manifestDir(sideload);
        File[] files = dir == null ? null : dir.listFiles();
        StringBuilder out = new StringBuilder();
        out.append("Установленные сабмоды:");
        int n = 0;
        if (files != null) {
            for (int i = 0; i < files.length; i++) {
                File file = files[i];
                if (file == null || !file.isFile()) {
                    continue;
                }
                String name = file.getName();
                if (name == null || !name.endsWith(".json")) {
                    continue;
                }
                try {
                    JSONObject man = new JSONObject(readText(file));
                    n++;
                    out.append("\n").append(n).append(". ");
                    out.append(man.optString("pack", name));
                    out.append("  id=").append(man.optString("id", ""));
                    out.append("  файлов ").append(man.optInt("files", 0));
                    out.append("  новых ").append(arrayLen(man.optJSONArray("added")));
                    out.append("  замен ").append(arrayLen(man.optJSONArray("replaced")));
                } catch (Exception ignored) {
                }
            }
        }
        if (n == 0) {
            out.append("\nпока нет. Поставь zip или ссылку GitHub.");
        } else {
            out.append("\nСнять пак можно карточкой ниже — остальные сабмоды остаются.");
        }
        return out.toString();
    }

    public static String listJson(File sideload) {
        File dir = manifestDir(sideload);
        File[] files = dir == null ? null : dir.listFiles();
        JSONArray arr = new JSONArray();
        if (files != null) {
            for (int i = 0; i < files.length; i++) {
                File file = files[i];
                if (file == null || !file.isFile()) {
                    continue;
                }
                String name = file.getName();
                if (name == null || !name.endsWith(".json")) {
                    continue;
                }
                try {
                    JSONObject man = new JSONObject(readText(file));
                    JSONObject row = new JSONObject();
                    row.put("id", man.optString("id", name.substring(0, name.length() - 5)));
                    row.put("pack", man.optString("pack", row.getString("id")));
                    row.put("files", man.optInt("files", 0));
                    row.put("added", arrayLen(man.optJSONArray("added")));
                    row.put("replaced", arrayLen(man.optJSONArray("replaced")));
                    row.put("kind", man.optString("kind", "submod"));
                    arr.put(row);
                } catch (Exception ignored) {
                }
            }
        }
        return arr.toString();
    }

    public static String lastId(File sideload) {
        File dir = manifestDir(sideload);
        File[] files = dir == null ? null : dir.listFiles();
        if (files == null) {
            return "";
        }
        File best = null;
        long bestTime = -1L;
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null || !file.isFile()) {
                continue;
            }
            String name = file.getName();
            if (name == null || !name.endsWith(".json")) {
                continue;
            }
            long when = file.lastModified();
            if (best == null || when > bestTime) {
                best = file;
                bestTime = when;
            }
        }
        if (best == null) {
            return "";
        }
        String name = best.getName();
        return name.substring(0, name.length() - 5);
    }

    public static String rewriteGithubUrl(String url) {
        if (url == null) {
            return "";
        }
        String u = url.trim();
        if (u.length() == 0) {
            return "";
        }
        if (u.startsWith("www.")) {
            u = "https://" + u;
        }
        if (u.matches("(?i)github\\.com/.*")) {
            u = "https://" + u;
        }
        if (u.endsWith(".git")) {
            u = u.substring(0, u.length() - 4);
        }
        while (u.endsWith("/")) {
            u = u.substring(0, u.length() - 1);
        }
        if (u.matches("(?i)https://(www\\.)?github\\.com/[^/]+/[^/]+")) {
            u = u.replaceFirst("(?i)https://www\\.", "https://");
            return u + "/archive/refs/heads/main.zip";
        }
        java.util.regex.Matcher tree = java.util.regex.Pattern
                .compile("(?i)https://(?:www\\.)?github\\.com/([^/]+)/([^/]+)/tree/([^/]+)")
                .matcher(u);
        if (tree.matches()) {
            return "https://github.com/" + tree.group(1) + "/" + tree.group(2)
                    + "/archive/refs/heads/" + tree.group(3) + ".zip";
        }
        return u;
    }

    private static void appendKeys(JSONArray into, JSONArray src) {
        if (src == null) {
            return;
        }
        for (int i = 0; i < src.length(); i++) {
            String key = src.optString(i, "");
            if (key != null && key.length() > 0) {
                into.put(key);
            }
        }
    }

    /**
     * Recompute the live overlay file after removing one submod.
     * @return 1 restored, -1 deleted, 0 unchanged
     */
    private static int restoreLive(Dest dest, String exceptId, File gameOverlay, File sideload) {
        File base = rootFor(dest, gameOverlay, sideload);
        File out = new File(base, dest.rel);
        File otherPay = newestOtherPayload(dest.key(), exceptId, sideload);
        if (otherPay != null && otherPay.isFile()) {
            File parent = out.getParentFile();
            if (parent != null && !parent.isDirectory()) {
                parent.mkdirs();
            }
            try {
                copyFile(otherPay, out);
                deleteCompiledTwins(out);
                return 1;
            } catch (Exception e) {
                return 0;
            }
        }
        File vanilla = vanillaFile(sideload, dest);
        if (vanilla.isFile()) {
            File parent = out.getParentFile();
            if (parent != null && !parent.isDirectory()) {
                parent.mkdirs();
            }
            try {
                copyFile(vanilla, out);
                deleteCompiledTwins(out);
                return 1;
            } catch (Exception e) {
                return 0;
            }
        }
        deleteCompiledTwins(out);
        boolean gone = false;
        if (out.isFile()) {
            gone = out.delete();
        }
        if (gone) {
            pruneEmpty(out.getParentFile(), base);
            return -1;
        }
        return 0;
    }

    private static File newestOtherPayload(String key, String exceptId, File sideload) {
        File dir = manifestDir(sideload);
        File[] files = dir == null ? null : dir.listFiles();
        if (files == null) {
            return null;
        }
        File bestPay = null;
        long bestAt = -1L;
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null || !file.isFile()) {
                continue;
            }
            String name = file.getName();
            if (name == null || !name.endsWith(".json")) {
                continue;
            }
            String oid = name.substring(0, name.length() - 5);
            if (oid.equals(exceptId)) {
                continue;
            }
            try {
                JSONObject man = new JSONObject(readText(file));
                if (!arrayHas(man.optJSONArray("added"), key)
                        && !arrayHas(man.optJSONArray("replaced"), key)) {
                    continue;
                }
                long at = man.optLong("installedAt", file.lastModified());
                Dest dest = Dest.parse(key);
                if (dest == null) {
                    continue;
                }
                File pay = payloadFile(sideload, oid, dest);
                if (!pay.isFile()) {
                    continue;
                }
                if (bestPay == null || at >= bestAt) {
                    bestPay = pay;
                    bestAt = at;
                }
            } catch (Exception ignored) {
            }
        }
        return bestPay;
    }

    private static boolean otherOwnsKey(String key, String exceptId, File sideload) {
        File dir = manifestDir(sideload);
        File[] files = dir == null ? null : dir.listFiles();
        if (files == null || key == null || key.length() == 0) {
            return false;
        }
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null || !file.isFile()) {
                continue;
            }
            String name = file.getName();
            if (name == null || !name.endsWith(".json")) {
                continue;
            }
            String oid = name.substring(0, name.length() - 5);
            if (oid.equals(exceptId)) {
                continue;
            }
            try {
                JSONObject man = new JSONObject(readText(file));
                if (arrayHas(man.optJSONArray("added"), key)
                        || arrayHas(man.optJSONArray("replaced"), key)) {
                    return true;
                }
            } catch (Exception ignored) {
            }
        }
        return false;
    }

    private static boolean arrayHas(JSONArray arr, String key) {
        if (arr == null || key == null) {
            return false;
        }
        for (int i = 0; i < arr.length(); i++) {
            if (key.equals(arr.optString(i, ""))) {
                return true;
            }
        }
        return false;
    }

    private static String normalize(String name) {
        String n = name.replace('\\', '/');
        while (n.startsWith("/")) {
            n = n.substring(1);
        }
        return n;
    }

    private static boolean junkZipName(String name) {
        if (name == null || name.length() == 0) {
            return true;
        }
        String n = normalize(name);
        if (n.startsWith("/") || n.indexOf("..") >= 0) {
            return true;
        }
        String low = n.toLowerCase(Locale.US);
        if (low.startsWith("__macosx/") || low.contains("/__macosx/")) {
            return true;
        }
        if (low.startsWith(".git/") || low.contains("/.git/")) {
            return true;
        }
        if (low.endsWith(".ds_store") || low.endsWith("/thumbs.db")) {
            return true;
        }
        return false;
    }

    private static String commonPrefix(List<String> names) {
        if (names == null || names.isEmpty()) {
            return "";
        }
        String first = names.get(0);
        int slash = first.indexOf('/');
        if (slash <= 0) {
            return "";
        }
        String top = first.substring(0, slash + 1);
        String low = top.toLowerCase(Locale.US);
        if (low.equals("game/") || low.equals("submods/") || low.equals("mod_assets/")
                || low.equals("python-packages/") || low.equals("saves/")
                || low.equals("characters/") || low.equals("gui/")
                || low.equals("custom_bgm/") || low.equals("chess_games/")
                || low.equals("piano_songs/")) {
            return "";
        }
        for (int i = 0; i < names.size(); i++) {
            String n = names.get(i);
            if (n == null || !n.regionMatches(true, 0, top, 0, top.length())) {
                return "";
            }
        }
        return top;
    }

    private static String peel(String path, String prefix) {
        String p = path;
        if (prefix != null && prefix.length() > 0 && p.regionMatches(true, 0, prefix, 0, prefix.length())) {
            p = p.substring(prefix.length());
        }
        String low = p.toLowerCase(Locale.US);
        String[] markers = new String[] {
                "/game/submods/", "/game/mod_assets/", "/game/python-packages/",
                "/game/gui/",
                "game/submods/", "game/mod_assets/", "game/python-packages/",
                "game/gui/",
                "/submods/", "/mod_assets/", "/python-packages/",
                "submods/", "mod_assets/", "python-packages/",
                "/characters/", "characters/",
                "/custom_bgm/", "custom_bgm/",
                "/chess_games/", "/piano_songs/"
        };
        for (int i = 0; i < markers.length; i++) {
            String m = markers[i];
            if (m.startsWith("/")) {
                int idx = low.indexOf(m);
                if (idx >= 0) {
                    return p.substring(idx + 1);
                }
            } else if (low.startsWith(m)) {
                return p;
            }
        }
        return p;
    }

    private static class Dest {
        String root;
        String rel;

        Dest(String root, String rel) {
            this.root = root;
            this.rel = rel;
        }

        String key() {
            return root + ":" + rel;
        }

        static Dest parse(String key) {
            if (key == null || key.length() == 0) {
                return null;
            }
            int colon = key.indexOf(':');
            if (colon <= 0) {
                return new Dest("game", key);
            }
            return new Dest(key.substring(0, colon), key.substring(colon + 1));
        }
    }

    private static File rootFor(Dest dest, File gameOverlay, File sideload) {
        if (dest != null && "docs".equals(dest.root)) {
            return sideload;
        }
        return gameOverlay;
    }

    private static File backupFile(File backupDir, Dest dest) {
        return new File(backupDir, dest.root + "/" + dest.rel);
    }

    private static String classifyKind(List<String> names) {
        if (names == null || names.isEmpty()) {
            return "submod";
        }
        int sub = 0;
        int sprite = 0;
        int asset = 0;
        int rpy = 0;
        int gift = 0;
        for (int i = 0; i < names.size(); i++) {
            String low = names.get(i).toLowerCase(Locale.US);
            String leaf = leafName(low);
            if (leaf.endsWith(".rpy") || leaf.endsWith(".rpym")
                    || low.contains("/submods/") || low.startsWith("submods/")) {
                sub += 4;
                if (leaf.endsWith(".rpy") || leaf.endsWith(".rpym")) {
                    rpy++;
                }
            }
            if (low.contains("mod_assets/monika/")
                    || low.contains("/monika/j/")
                    || low.contains("/monika/c/")
                    || low.contains("/monika/a/")
                    || low.contains("/monika/h/")
                    || low.contains("/monika/f/")
                    || low.contains("/hair/")
                    || low.contains("/clothes/")
                    || low.contains("/acs/")
                    || leaf.startsWith("hair-")
                    || leaf.startsWith("acs-")
                    || leaf.startsWith("clothes-")) {
                sprite += 3;
            }
            if (leaf.endsWith(".json")) {
                sprite += 2;
            }
            if (leaf.endsWith(".gift")) {
                gift++;
                sprite += 2;
            }
            if (knownAsset(leaf) != null) {
                asset += 5;
            } else if (leaf.endsWith(".png") || leaf.endsWith(".jpg")
                    || leaf.endsWith(".jpeg") || leaf.endsWith(".webp")
                    || leaf.endsWith(".ogg") || leaf.endsWith(".mp3")
                    || leaf.endsWith(".wav")) {
                asset += 1;
            }
        }
        if (sub > 0) {
            if (rpy <= 2 && sprite >= 8) {
                return "spritepack";
            }
            return "submod";
        }
        if (gift > 0 && sprite >= 2) {
            return "spritepack";
        }
        if (sprite >= 3 && sprite >= asset) {
            return "spritepack";
        }
        if (asset > 0) {
            return "assetpack";
        }
        return "submod";
    }

    private static boolean looksSprite(List<String> names) {
        if (names == null) {
            return false;
        }
        boolean json = false;
        boolean art = false;
        boolean gift = false;
        for (int i = 0; i < names.size(); i++) {
            String low = names.get(i).toLowerCase(Locale.US);
            if (low.contains("mod_assets/monika/j/")
                    || low.contains("/monika/j/")
                    || low.contains("mod_assets/monika/c/")
                    || low.contains("mod_assets/monika/a/")
                    || low.contains("mod_assets/monika/h/")) {
                return true;
            }
            if (low.endsWith(".json")) {
                json = true;
            }
            if (low.endsWith(".png") || low.endsWith(".jpg")
                    || low.endsWith(".jpeg") || low.endsWith(".webp")) {
                art = true;
            }
            String leaf = leafName(low);
            if (leaf.endsWith(".gift") || (leaf.indexOf('.') < 0 && leaf.length() > 0)) {
                gift = true;
            }
        }
        return json && (art || gift);
    }

    private static boolean looksSubmod(List<String> names) {
        if (names == null) {
            return false;
        }
        for (int i = 0; i < names.size(); i++) {
            String low = names.get(i).toLowerCase(Locale.US);
            if (low.contains("/submods/") || low.startsWith("submods/")
                    || low.endsWith(".rpy") || low.endsWith(".rpym")) {
                return true;
            }
        }
        return false;
    }

    private static boolean looksAssetPack(List<String> names) {
        if (names == null || names.isEmpty()) {
            return false;
        }
        int art = 0;
        for (int i = 0; i < names.size(); i++) {
            String low = names.get(i).toLowerCase(Locale.US);
            String leaf = leafName(low);
            if (leaf.endsWith(".rpy") || leaf.endsWith(".rpym")
                    || leaf.endsWith(".json")) {
                return false;
            }
            if (leaf.endsWith(".png") || leaf.endsWith(".jpg")
                    || leaf.endsWith(".jpeg") || leaf.endsWith(".webp")
                    || leaf.endsWith(".ogg") || leaf.endsWith(".mp3")
                    || leaf.endsWith(".wav")) {
                art++;
            }
        }
        return art > 0;
    }

    private static String knownAsset(String leaf) {
        if (leaf == null) {
            return null;
        }
        String low = leaf.toLowerCase(Locale.US);
        if (low.equals("pong.png")) {
            return "mod_assets/games/pong/pong.png";
        }
        if (low.equals("pong_field.png")) {
            return "mod_assets/games/pong/pong_field.png";
        }
        if (low.equals("pong_ball.png")) {
            return "mod_assets/games/pong/pong_ball.png";
        }
        if (low.equals("chess_board.png")) {
            return "mod_assets/games/chess/chess_board.png";
        }
        if (low.equals("piano.png") || low.equals("board.png")) {
            if (low.equals("piano.png")) {
                return "mod_assets/games/piano/piano.png";
            }
            return "mod_assets/games/piano/board.png";
        }
        if (low.startsWith("hm_") && low.endsWith(".png")) {
            return "mod_assets/games/hangman/" + leaf;
        }
        return null;
    }

    private static void collectLeaf(File dir, String leaf, int depth, List<File> out) {
        if (dir == null || !dir.isDirectory() || depth > 8 || out.size() > 1) {
            return;
        }
        File[] kids = dir.listFiles();
        if (kids == null) {
            return;
        }
        for (int i = 0; i < kids.length; i++) {
            File kid = kids[i];
            if (kid == null) {
                continue;
            }
            if (kid.isDirectory()) {
                collectLeaf(kid, leaf, depth + 1, out);
                continue;
            }
            if (leaf.equalsIgnoreCase(kid.getName())) {
                out.add(kid);
                if (out.size() > 1) {
                    return;
                }
            }
        }
    }

    private static String relativeTo(File root, File file) {
        try {
            String base = root.getCanonicalPath();
            String path = file.getCanonicalPath();
            if (path.equals(base)) {
                return "";
            }
            if (path.startsWith(base + File.separator)) {
                return path.substring(base.length() + 1).replace('\\', '/');
            }
        } catch (Exception ignored) {
        }
        return null;
    }

    private static Dest mapAssetDest(String peeled, File overlay) {
        String leaf = leafName(peeled);
        String known = knownAsset(leaf);
        if (known != null) {
            return new Dest("game", known);
        }
        String low = peeled.toLowerCase(Locale.US);
        if (low.startsWith("mod_assets/") || low.startsWith("gui/")
                || low.startsWith("images/")) {
            return new Dest("game", peeled);
        }
        if (overlay != null && overlay.isDirectory() && leaf.length() > 0) {
            List<File> found = new ArrayList<File>();
            collectLeaf(overlay, leaf, 0, found);
            if (found.size() == 1) {
                String rel = relativeTo(overlay, found.get(0));
                if (rel != null && rel.length() > 0) {
                    return new Dest("game", rel);
                }
            }
        }
        return null;
    }

    private static Dest destFor(String peeled, String pack, boolean asSprite, boolean asAsset, File overlay) {
        if (peeled == null || peeled.length() == 0) {
            return null;
        }
        String rel = peeled;
        String low = rel.toLowerCase(Locale.US);
        if (low.startsWith("game/")) {
            rel = rel.substring(5);
            low = rel.toLowerCase(Locale.US);
        }
        if (low.length() == 0) {
            return null;
        }
        if (low.startsWith("characters/") || low.startsWith("custom_bgm/")
                || low.startsWith("chess_games/") || low.startsWith("piano_songs/")
                || low.startsWith("saves/")) {
            return new Dest("docs", rel);
        }
        if (low.startsWith("submods/")) {
            String rest = rel.substring("submods/".length());
            if (rest.length() == 0) {
                return null;
            }
            return new Dest("game", "Submods/" + rest);
        }
        if (low.startsWith("mod_assets/") || low.startsWith("python-packages/")
                || low.startsWith("gui/")) {
            return new Dest("game", rel);
        }
        if (asSprite) {
            if (low.startsWith("j/") || low.startsWith("a/") || low.startsWith("c/")
                    || low.startsWith("h/") || low.startsWith("f/") || low.startsWith("t/")) {
                return new Dest("game", "mod_assets/monika/" + rel);
            }
            int jAt = low.lastIndexOf("/j/");
            if (jAt >= 0 && low.endsWith(".json")) {
                return new Dest("game", "mod_assets/monika/" + rel.substring(jAt + 1));
            }
            if (low.endsWith(".json")) {
                return new Dest("game", "mod_assets/monika/j/" + leafName(rel));
            }
            String leaf = leafName(rel);
            String leafLow = leaf.toLowerCase(Locale.US);
            if (leafLow.endsWith(".gift") || (leaf.indexOf('.') < 0 && leaf.length() > 0)) {
                return new Dest("docs", "characters/" + leaf);
            }
            if (leafLow.endsWith(".png") || leafLow.endsWith(".jpg")
                    || leafLow.endsWith(".jpeg") || leafLow.endsWith(".webp")) {
                return new Dest("game", "mod_assets/monika/" + rel);
            }
            return new Dest("game", "mod_assets/monika/" + pack + "/" + rel);
        }
        if (asAsset) {
            return mapAssetDest(rel, overlay);
        }
        return new Dest("game", "Submods/" + pack + "/" + rel);
    }

    private static String leafName(String rel) {
        String n = rel == null ? "" : rel.replace('\\', '/');
        int slash = n.lastIndexOf('/');
        if (slash >= 0) {
            n = n.substring(slash + 1);
        }
        return n;
    }

    private static void deleteCompiledTwins(File out) {
        if (out == null) {
            return;
        }
        File parent = out.getParentFile();
        String name = out.getName();
        if (parent == null || name == null) {
            return;
        }
        if (name.endsWith(".rpy") || name.endsWith(".rpym")) {
            new File(parent, name + "c").delete();
        }
    }

    private static void dropOwnedTrees(JSONArray keys, String exceptId,
            File gameOverlay, File sideload) {
        if (keys == null || gameOverlay == null) {
            return;
        }
        java.util.HashSet<String> packs = new java.util.HashSet<String>();
        for (int i = 0; i < keys.length(); i++) {
            Dest dest = Dest.parse(keys.optString(i, ""));
            if (dest == null || dest.rel == null || !"game".equals(dest.root)) {
                continue;
            }
            String rel = dest.rel.replace('\\', '/');
            String low = rel.toLowerCase(Locale.US);
            if (!low.startsWith("submods/")) {
                continue;
            }
            String rest = rel.substring("submods/".length());
            int slash = rest.indexOf('/');
            String pack = slash < 0 ? rest : rest.substring(0, slash);
            if (pack.length() > 0) {
                packs.add(pack);
            }
        }
        java.util.Iterator<String> it = packs.iterator();
        while (it.hasNext()) {
            String pack = it.next();
            if (otherOwnsPrefix("game:Submods/" + pack, exceptId, sideload)) {
                continue;
            }
            deleteTree(new File(gameOverlay, "Submods/" + pack));
        }
    }

    private static boolean otherOwnsPrefix(String prefix, String exceptId, File sideload) {
        File dir = manifestDir(sideload);
        File[] files = dir == null ? null : dir.listFiles();
        if (files == null || prefix == null) {
            return false;
        }
        String p = prefix.toLowerCase(Locale.US);
        String pSlash = p.endsWith("/") ? p : p + "/";
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null || !file.isFile()) {
                continue;
            }
            String name = file.getName();
            if (name == null || !name.endsWith(".json")) {
                continue;
            }
            String oid = name.substring(0, name.length() - 5);
            if (oid.equals(exceptId)) {
                continue;
            }
            try {
                JSONObject man = new JSONObject(readText(file));
                JSONArray keys = new JSONArray();
                appendKeys(keys, man.optJSONArray("added"));
                appendKeys(keys, man.optJSONArray("replaced"));
                for (int k = 0; k < keys.length(); k++) {
                    String key = keys.optString(k, "").toLowerCase(Locale.US);
                    if (key.equals(p) || key.startsWith(pSlash)) {
                        return true;
                    }
                }
            } catch (Exception ignored) {
            }
        }
        return false;
    }

    private static void pruneEmpty(File dir, File stop) {
        File cursor = dir;
        while (cursor != null && cursor.isDirectory()) {
            try {
                if (stop != null && cursor.getCanonicalPath().equals(stop.getCanonicalPath())) {
                    break;
                }
            } catch (Exception e) {
                break;
            }
            String[] kids = cursor.list();
            if (kids != null && kids.length > 0) {
                break;
            }
            File parent = cursor.getParentFile();
            cursor.delete();
            cursor = parent;
        }
    }

    private static String packName(String zipName, String prefix) {
        String name = zipName == null ? "submod" : zipName;
        int slash = name.replace('\\', '/').lastIndexOf('/');
        if (slash >= 0) {
            name = name.substring(slash + 1);
        }
        String low = name.toLowerCase(Locale.US);
        if (low.endsWith(".zip")) {
            name = name.substring(0, name.length() - 4);
        }
        if (prefix != null && prefix.length() > 1) {
            String p = prefix.substring(0, prefix.length() - 1);
            if (p.length() > 0) {
                name = p;
            }
        }
        name = name.replaceAll("(?i)-main$", "");
        name = name.replaceAll("(?i)-master$", "");
        name = name.replaceAll("[^A-Za-z0-9._-]+", "_");
        if (name.length() == 0) {
            name = "submod";
        }
        if (name.length() > 40) {
            name = name.substring(0, 40);
        }
        return name;
    }

    private static String safeId(String pack) {
        String id = pack == null ? "submod" : pack.toLowerCase(Locale.US);
        id = id.replaceAll("[^a-z0-9._-]+", "_");
        if (id.length() == 0) {
            id = "submod";
        }
        return id;
    }

    private static boolean staysInside(File root, File candidate) {
        try {
            String base = root.getCanonicalPath();
            String target = candidate.getCanonicalPath();
            return target.equals(base) || target.startsWith(base + File.separator);
        } catch (Exception e) {
            return false;
        }
    }

    private static int arrayLen(JSONArray arr) {
        return arr == null ? 0 : arr.length();
    }

    private static void copyEntry(ZipFile zipFile, ZipEntry entry, File out) throws Exception {
        InputStream in = null;
        FileOutputStream outs = null;
        try {
            in = zipFile.getInputStream(entry);
            outs = new FileOutputStream(out);
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) >= 0) {
                if (n > 0) {
                    outs.write(buf, 0, n);
                }
            }
        } finally {
            if (in != null) {
                try {
                    in.close();
                } catch (Exception ignored) {
                }
            }
            if (outs != null) {
                try {
                    outs.close();
                } catch (Exception ignored) {
                }
            }
        }
    }

    private static void copyFile(File src, File dest) throws Exception {
        if (src == null || dest == null || src.getAbsolutePath().equals(dest.getAbsolutePath())) {
            return;
        }
        File parent = dest.getParentFile();
        if (parent != null && !parent.isDirectory()) {
            parent.mkdirs();
        }
        FileInputStream in = null;
        FileOutputStream out = null;
        try {
            in = new FileInputStream(src);
            out = new FileOutputStream(dest);
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) >= 0) {
                if (n > 0) {
                    out.write(buf, 0, n);
                }
            }
        } finally {
            if (in != null) {
                try {
                    in.close();
                } catch (Exception ignored) {
                }
            }
            if (out != null) {
                try {
                    out.close();
                } catch (Exception ignored) {
                }
            }
        }
    }

    private static void deleteTree(File dir) {
        if (dir == null || !dir.exists()) {
            return;
        }
        File[] files = dir.listFiles();
        if (files != null) {
            for (int i = 0; i < files.length; i++) {
                File file = files[i];
                if (file == null) {
                    continue;
                }
                if (file.isDirectory()) {
                    deleteTree(file);
                } else {
                    file.delete();
                }
            }
        }
        dir.delete();
    }

    private static void writeText(File file, String text) throws Exception {
        FileOutputStream out = new FileOutputStream(file);
        try {
            out.write(text.getBytes("UTF-8"));
        } finally {
            out.close();
        }
    }

    private static String readText(File file) throws Exception {
        FileInputStream in = new FileInputStream(file);
        try {
            byte[] buf = new byte[(int) Math.max(file.length(), 1)];
            int got = 0;
            int n;
            while (got < buf.length && (n = in.read(buf, got, buf.length - got)) >= 0) {
                if (n > 0) {
                    got += n;
                }
            }
            return new String(buf, 0, got, "UTF-8");
        } finally {
            in.close();
        }
    }
}
