// MAS BIOS: экран до Ren'Py. Documents/Monika_after_story, WebView из
// getFilesDir()/bios_www, игра в процессе :game (PythonSDLActivity).

package ru.kurokawa.mas.bios;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ClipData;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.provider.DocumentsContract;
import android.provider.OpenableColumns;
import android.support.v4.content.FileProvider;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.provider.Settings;
import android.view.View;
import android.webkit.JavascriptInterface;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;

import org.renpy.android.PythonSDLActivity;
import org.renpy.android.R;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONArray;
import org.json.JSONObject;

import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.Enumeration;
import java.util.List;
import java.util.Locale;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;
import java.util.zip.ZipOutputStream;

public class LauncherActivity extends Activity {

    private static final int REQ_STORAGE = 41;
    private static final int REQ_PICK_IMAGE = 81;
    private static final int REQ_PICK_ZIP = 82;
    private static final int REQ_PICK_FILE = 83;
    private static final int REQ_PICK_RPA = 84;
    private static final int REQ_PICK_SUBMOD = 85;
    private static final int REQ_PICK_SAVES_ZIP = 86;
    private static final int REQ_PICK_SAVES_DIR = 87;
    private static final String RELEASES_URL =
            "https://api.github.com/repos/artem213101zse/MonikaModDev-RU/releases/latest";

    private volatile String updateApkUrl;
    private volatile String updateApkName;
    private volatile String updateApkDigest;
    private volatile String updateApkShaUrl;
    private volatile long updateAssetSize = -1L;
    private volatile boolean updateNeeded = true;

    private boolean downloadRunning = false;
    private volatile boolean downloadCancel = false;
    private volatile boolean downloadPaused = false;
    private String lastDownloadUrl;
    private File lastDownloadDest;
    private String lastDownloadHash;
    private boolean lastDownloadRequireZip;
    private boolean engineBusy = false;
    private Process stockfishProc;
    private InputStream stockfishRaw;
    private BufferedReader stockfishReader;
    private OutputStream stockfishStdin;

    private TextView statusView;
    private TextView pathView;
    private TextView progressLine;
    private ProgressBar progressBar;
    private WebView webView;
    private boolean pageReady = false;
    private boolean nativeShown = false;
    private final StringBuilder webBuffer = new StringBuilder();
    private File sideloadDir;
    private File incomingDir;
    private File logFile;
    private String biosByteSource = "none";
    private boolean biosPrepareAttempted = false;
    private String pendingOpen = "play";
    private boolean pageOpened = false;
    private File transferDir;
    private String pickDestKind = "auto";
    private File gameOverlayDir;
    private File archivesDir;
    private boolean hidingForGame = false;
    private boolean foldersPrepared = false;
    private org.json.JSONArray archivePacks;
    private static final String DOCS_FLAG = ".use_documents_saves";
    private static final String APP_SAVES_FLAG = ".use_app_saves";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        resolvePaths();
        Intent launched = getIntent();
        boolean forceBios = launched != null && launched.getBooleanExtra("force_bios", false);
        boolean skipUi = launched != null && launched.getBooleanExtra("boot_renpy", false);
        if (launched != null) {
            String open = launched.getStringExtra("open");
            if (open != null && open.length() > 0) {
                pendingOpen = open;
            }
        }
        if (!forceBios && (skipUi || flagExists("boot_renpy"))
                && canUseDocuments() && archivesReady()) {
            hidingForGame = true;
            ensureDocumentsFlag();
            ensureLayout();
            installNativeEngine();
            installMbaseFile();
            startGame();
            return;
        }
        if (flagExists("ui_native")) {
            showNativeBios();
        } else if (!tryShowWebBios()) {
            File missing = new File(new File(getFilesDir(), "bios_www"), "index.html");
            showWebFailed("exists=false", missing.getAbsolutePath());
        }

        installNativeEngine();
        if (!canUseDocuments()) {
            setStatus("Нужен доступ ко всем файлам.\n"
                    + "MAS пишет в Documents/Monika_after_story: архивы, сейвы, подарки, музыку.\n"
                    + "Без разрешения Android не пустит в Документы, и игра не увидит картинки.\n"
                    + pathReport());
            if (needsRuntimePermission()) {
                requestPermissions(new String[] {
                        android.Manifest.permission.READ_EXTERNAL_STORAGE,
                        android.Manifest.permission.WRITE_EXTERNAL_STORAGE
                }, REQ_STORAGE);
            }
            pushStatusToPage();
            return;
        }
        ensureDocumentsFlag();
        prepareFolders();
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        applyLaunchExtras(intent);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (hidingForGame) {
            hidingForGame = false;
            return;
        }
        if (webView == null && !nativeShown) {
            ensureBiosUi();
        }
        if (canUseDocuments()) {
            ensureDocumentsFlag();
            if (!foldersPrepared) {
                prepareFolders();
            } else {
                runHealthReport(false);
                pushStatusToPage();
            }
        } else {
            pushStatusToPage();
        }
    }

    private void applyLaunchExtras(Intent intent) {
        if (intent == null) {
            return;
        }
        boolean forceBios = intent.getBooleanExtra("force_bios", false);
        boolean bootRenpy = intent.getBooleanExtra("boot_renpy", false);
        String open = intent.getStringExtra("open");
        if (open != null && open.length() > 0) {
            pendingOpen = open;
        }
        if (bootRenpy && !forceBios && canUseDocuments() && archivesReady()) {
            hidingForGame = true;
            startGame();
            return;
        }
        ensureBiosUi();
        if (webView != null && pageReady && pendingOpen != null) {
            evalJs("biosOpen", pendingOpen);
            pushStatusToPage();
        }
    }

    private void ensureBiosUi() {
        if (webView != null || nativeShown) {
            return;
        }
        if (flagExists("ui_native")) {
            showNativeBios();
        } else if (!tryShowWebBios()) {
            File missing = new File(new File(getFilesDir(), "bios_www"), "index.html");
            showWebFailed("exists=false", missing.getAbsolutePath());
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_PICK_IMAGE && requestCode != REQ_PICK_ZIP
                && requestCode != REQ_PICK_FILE && requestCode != REQ_PICK_RPA
                && requestCode != REQ_PICK_SUBMOD && requestCode != REQ_PICK_SAVES_ZIP
                && requestCode != REQ_PICK_SAVES_DIR) {
            return;
        }
        if (resultCode != RESULT_OK || data == null || data.getData() == null) {
            appendStatus("\nотмена");
            logLine("picker cancel");
            return;
        }
        if (requestCode == REQ_PICK_IMAGE) {
            copyWallpaper(data.getData());
        } else if (requestCode == REQ_PICK_FILE) {
            copyPickedFile(data.getData());
        } else if (requestCode == REQ_PICK_RPA) {
            copyPickedArchive(data.getData());
        } else if (requestCode == REQ_PICK_SUBMOD) {
            copyPickedSubmod(data.getData());
        } else if (requestCode == REQ_PICK_SAVES_ZIP) {
            importPickedSavesZip(data.getData());
        } else if (requestCode == REQ_PICK_SAVES_DIR) {
            importPickedSavesFolder(data.getData());
        } else {
            copyPickedSubmod(data.getData());
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode != REQ_STORAGE) {
            return;
        }
        boolean granted = true;
        if (grantResults == null || grantResults.length == 0) {
            granted = false;
        } else {
            for (int i = 0; i < grantResults.length; i++) {
                if (grantResults[i] != PackageManager.PERMISSION_GRANTED) {
                    granted = false;
                }
            }
        }
        if (!granted) {
            showPath();
            setStatus("Нет права на память. Папки не созданы.\n"
                    + "MAS не сможет писать в Documents/Monika_after_story.\n"
                    + pathReport());
            pushStatusToPage();
            return;
        }
        ensureDocumentsFlag();
        prepareFolders();
    }

    private File nativeLibDirFile() {
        try {
            String dir = getApplicationInfo().nativeLibraryDir;
            if (dir != null && dir.length() > 0) {
                return new File(dir);
            }
        } catch (Exception ignored) {
        }
        return new File(getFilesDir(), "lib");
    }

    private File nativeSo(String soName) {
        return new File(nativeLibDirFile(), soName);
    }

    private File resolveEngineBinary(String soName, String filesName) {
        File so = nativeSo(soName);
        if (so.isFile()) {
            return so;
        }
        File files = new File(getFilesDir(), filesName);
        if (files.isFile()) {
            return files;
        }
        return so;
    }

    private String describeFile(File f) {
        if (f == null) {
            return "(нет пути)";
        }
        if (!f.isFile()) {
            return f.getAbsolutePath() + " — файла нет";
        }
        return f.getAbsolutePath()
                + " (" + f.length() + " байт)"
                + " r=" + f.canRead()
                + " x=" + f.canExecute();
    }

    private void writeEnginePaths(File hello, File stock) {
        FileWriter w = null;
        try {
            File marker = new File(getFilesDir(), "engine_paths.txt");
            w = new FileWriter(marker);
            if (hello != null) {
                w.write("hello_engine=" + hello.getAbsolutePath() + "\n");
            }
            if (stock != null) {
                w.write("stockfish=" + stock.getAbsolutePath() + "\n");
            }
            w.write("libdir=" + nativeLibDirFile().getAbsolutePath() + "\n");
            w.flush();
            logLine("engine_paths " + marker.getAbsolutePath());
        } catch (Exception e) {
            logLine("engine_paths " + messageOf(e));
        } finally {
            if (w != null) {
                try {
                    w.close();
                } catch (Exception ignored) {
                }
            }
        }
    }

    private void installNativeEngine() {
        // Android 10+ (targetSdk 29+) блокирует exec из getFilesDir() — EACCES.
        // Запуск идёт из nativeLibraryDir: libhello_engine.so / libstockfish.so.
        File libDir = nativeLibDirFile();
        postStatus("\nlibdir: " + libDir.getAbsolutePath());
        logLine("libdir " + libDir.getAbsolutePath());
        File[] listed = libDir.listFiles();
        if (listed == null || listed.length == 0) {
            postStatus("\nlibdir пустой или недоступен.");
        } else {
            int n = listed.length;
            if (n > 32) {
                n = 32;
            }
            for (int i = 0; i < n; i++) {
                File f = listed[i];
                postStatus("\n  " + f.getName() + " " + f.length());
            }
        }

        File hello = nativeSo("libhello_engine.so");
        File stock = nativeSo("libstockfish.so");
        if (!hello.isFile() || !stock.isFile()) {
            postStatus("\nso в nativeLibraryDir нет. На Android 10+ exec из files/ закрыт (error=13). Пересобери APK с jniLibs.");
            logLine("engine so missing in libdir");
        }
        postStatus("\nhello_engine: " + describeFile(hello));
        postStatus("\nstockfish: " + describeFile(stock));
        writeEnginePaths(hello, stock);
    }

    private String nativeAbiSuffix() {
        String abi = "";
        if (Build.VERSION.SDK_INT >= 21) {
            String[] abis = Build.SUPPORTED_ABIS;
            if (abis != null && abis.length > 0 && abis[0] != null) {
                abi = abis[0];
            }
        } else {
            abi = Build.CPU_ABI == null ? "" : Build.CPU_ABI;
        }
        abi = abi.toLowerCase(Locale.US);
        if (abi.startsWith("arm64")) {
            return "-arm64";
        }
        if (abi.startsWith("x86_64")) {
            return "-x86_64";
        }
        return null;
    }

    private String nativeEngineAssetName() {
        String suffix = nativeAbiSuffix();
        if (suffix == null) {
            return null;
        }
        return "hello_engine" + suffix;
    }

    private void copyEngineAsset(String assetName, String destName) {
        File dest = new File(getFilesDir(), destName);
        InputStream in = null;
        FileOutputStream out = null;
        try {
            in = openEngineStream(assetName);
            if (in == null) {
                postStatus("\n" + destName + ": " + assetName + " нет в assets APK.");
                logLine("engine asset missing " + assetName);
                return;
            }
            out = new FileOutputStream(dest);
            byte[] buf = new byte[8192];
            int n;
            long total = 0;
            while ((n = in.read(buf)) >= 0) {
                if (n > 0) {
                    out.write(buf, 0, n);
                    total += n;
                }
            }
            out.flush();
            closeQuietly(out);
            out = null;
            chmod755(dest);
            postStatus("\n" + destName + ": " + dest.getAbsolutePath() + " (" + total + " байт)");
            logLine("copied " + assetName + " -> " + dest.getAbsolutePath() + " bytes " + total);
        } catch (Exception e) {
            postStatus("\nНе удалось скопировать " + destName + ": " + messageOf(e));
            logLine("copy engine failed " + destName + " " + messageOf(e));
        } finally {
            closeQuietly(in);
            closeQuietly(out);
        }
    }

    private InputStream openEngineStream(String name) {
        String[] assets = new String[] {
                name,
                "bin/" + name,
                "x-" + name,
                "x-bin/x-" + name,
                "x-rapt-overlay/x-bin/x-" + name,
                "x-game/x-mod_assets/x-mas_os/x-bios/x-bin/x-" + name,
                "game/mod_assets/mas_os/bios/bin/" + name
        };
        for (int i = 0; i < assets.length; i++) {
            try {
                InputStream in = getAssets().open(assets[i]);
                logLine("engine asset " + assets[i]);
                return in;
            } catch (IOException ignored) {
            }
        }
        return null;
    }

    private File mbaseOverlayFile() {
        if (gameOverlayDir == null) {
            return new File("mbase");
        }
        return new File(new File(new File(gameOverlayDir, "mod_assets"), "monika"), "mbase");
    }

    private File charactersMonikaFile() {
        File root = sideloadDir != null ? sideloadDir : getFilesDir();
        return new File(new File(root, "characters"), "monika");
    }

    private InputStream openMbaseStream() {
        String[] assets = new String[] {
                "x-game/x-mod_assets/x-monika/x-mbase",
                "game/mod_assets/monika/mbase",
                "x-mod_assets/x-monika/x-mbase",
                "mod_assets/monika/mbase",
                "x-mbase",
                "mbase"
        };
        for (int i = 0; i < assets.length; i++) {
            try {
                InputStream in = getAssets().open(assets[i]);
                logLine("mbase asset " + assets[i]);
                return in;
            } catch (IOException ignored) {
            }
        }
        return null;
    }

    private void installMbaseFile() {
        if (gameOverlayDir == null) {
            logLine("mbase skip: no overlay");
            return;
        }
        File dest = mbaseOverlayFile();
        if (dest.isFile() && dest.length() > 1000L) {
            logLine("mbase overlay exists " + dest.length());
            return;
        }
        InputStream in = openMbaseStream();
        if (in == null) {
            logLine("mbase asset missing");
            return;
        }
        File parent = dest.getParentFile();
        if (parent != null && !parent.isDirectory()) {
            parent.mkdirs();
        }
        if (writeStream(in, dest)) {
            logLine("mbase -> " + dest.getAbsolutePath() + " " + dest.length());
        } else {
            logLine("mbase copy failed");
        }
    }

    private void testMonikaFileNow(boolean write) {
        appendStatus("\nDocuments: "
                + (sideloadDir == null ? "(нет)" : sideloadDir.getAbsolutePath()));
        appendStatus("\nдоступ ко всем файлам: " + canUseDocuments());
        File overlay = mbaseOverlayFile();
        File monika = charactersMonikaFile();
        appendStatus("\nmbase overlay: " + describeFile(overlay));
        appendStatus("\ncharacters/monika: " + describeFile(monika));

        InputStream probe = openMbaseStream();
        if (probe == null) {
            appendStatus("\nmbase в APK не найден. Игра не соберёт файл Моники без этого ассета.");
            pushStatusToPage();
            return;
        }
        closeQuietly(probe);
        appendStatus("\nmbase в APK есть.");

        if (!write) {
            appendStatus("\nпроверка без записи. Нажми «Файл Моники», чтобы эмулировать «взять с собой».");
            pushStatusToPage();
            return;
        }

        InputStream in = openMbaseStream();
        File parent = overlay.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
            closeQuietly(in);
            appendStatus("\nне создалась папка overlay для mbase: " + overlay.getAbsolutePath());
            pushStatusToPage();
            return;
        }
        boolean copied = writeStream(in, overlay);
        appendStatus("\nmbase из APK → overlay: "
                + (copied ? describeFile(overlay) : "не записался"));
        if (!copied) {
            pushStatusToPage();
            return;
        }

        File chars = monika.getParentFile();
        if (chars != null && !chars.isDirectory() && !chars.mkdirs()) {
            appendStatus("\nпапка characters не создалась: " + chars.getAbsolutePath());
            pushStatusToPage();
            return;
        }

        FileOutputStream out = null;
        FileInputStream mbaseIn = null;
        try {
            out = new FileOutputStream(monika);
            byte[] header = "1|num||MASBIOS|take-monika-probe|||".getBytes("UTF-8");
            out.write(header);
            mbaseIn = new FileInputStream(overlay);
            byte[] buf = new byte[8192];
            int n;
            long total = header.length;
            while ((n = mbaseIn.read(buf)) >= 0) {
                if (n > 0) {
                    out.write(buf, 0, n);
                    total += n;
                }
            }
            out.flush();
            appendStatus("\nзаписан characters/monika (" + total + " байт)");
        } catch (Exception e) {
            appendStatus("\nзапись monika: " + messageOf(e));
        } finally {
            closeQuietly(mbaseIn);
            closeQuietly(out);
        }

        appendStatus("\nпосле записи: " + describeFile(monika));
        FileInputStream chk = null;
        try {
            chk = new FileInputStream(monika);
            int first = chk.read();
            appendStatus("\nopen() прошёл, первый байт=" + first + ", размер=" + monika.length());
        } catch (Exception e) {
            appendStatus("\nopen() не прошёл: " + messageOf(e));
        } finally {
            closeQuietly(chk);
        }
        appendStatus("\nИгра при «взять с собой» пишет тот же путь. После пробы удали characters/monika, иначе MAS решит что Моника уже ушла.");
        pushStatusToPage();
    }

    private void pauseDownloadNow() {
        if (!downloadRunning) {
            appendStatus("\nСейчас ничего не качается.");
            return;
        }
        downloadPaused = true;
        pushDlState("paused");
        appendStatus("\nПауза. Включи VPN и нажми Продолжить, или Отмена.");
        logLine("download paused");
    }

    private void resumeDownloadNow() {
        if (!downloadRunning) {
            appendStatus("\nНечего продолжать. Запусти скачивание заново.");
            return;
        }
        downloadPaused = false;
        pushDlState("running");
        appendStatus("\nПродолжаю скачивание.");
        logLine("download resume");
    }

    private void cancelDownloadNow() {
        if (!downloadRunning && !downloadPaused) {
            appendStatus("\nСейчас ничего не качается.");
            return;
        }
        downloadCancel = true;
        downloadPaused = false;
        pushDlState("idle");
        appendStatus("\nОтменяю скачивание. .part будет удалён.");
        logLine("download cancel");
    }

    private void collectMonikaFiles(File dir, List<File> out, int depth) {
        if (dir == null || !dir.isDirectory() || depth > 6) {
            return;
        }
        File[] files = dir.listFiles();
        if (files == null) {
            return;
        }
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null) {
                continue;
            }
            String name = file.getName();
            if (name == null || name.startsWith(".")) {
                continue;
            }
            if (file.isDirectory()) {
                collectMonikaFiles(file, out, depth + 1);
                continue;
            }
            String low = name.toLowerCase(Locale.US);
            if (low.equals("monika") || low.equals("monika.chr")) {
                out.add(file);
            }
        }
    }

    private void recoverMonikaScanNow() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        File dest = charactersMonikaFile();
        List<File> found = new ArrayList<File>();
        collectMonikaFiles(sideloadDir, found, 0);
        StringBuilder out = new StringBuilder();
        out.append("\n=== рекавери Моники ===");
        out.append("\nнужный путь: ").append(dest.getAbsolutePath());
        out.append("\nна месте: ").append(dest.isFile()
                ? (dest.length() + " байт") : "нет");
        out.append("\nнайдено копий: ").append(found.size());
        for (int i = 0; i < found.size(); i++) {
            File file = found.get(i);
            out.append("\n  ").append(file.getAbsolutePath())
                    .append("  ").append(file.length()).append(" байт");
        }
        if (found.isEmpty()) {
            out.append("\nфайла monika в Documents нет. Можно собрать заново из mbase.");
        } else if (!dest.isFile()) {
            out.append("\nНажми «Вернуть в characters», BIOS перенесёт первый найденный файл.");
        }
        appendStatus(out.toString());
        logLine("recover scan found=" + found.size() + " dest=" + dest.isFile());
        pushStatusToPage();
    }

    private void recoverMonikaRestoreNow() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        File dest = charactersMonikaFile();
        if (dest.isFile() && dest.length() > 0) {
            appendStatus("\ncharacters/monika уже на месте (" + dest.length() + " байт).");
            pushStatusToPage();
            return;
        }
        List<File> found = new ArrayList<File>();
        collectMonikaFiles(sideloadDir, found, 0);
        File src = null;
        for (int i = 0; i < found.size(); i++) {
            File file = found.get(i);
            if (file == null || !file.isFile()) {
                continue;
            }
            if (file.getAbsolutePath().equals(dest.getAbsolutePath())) {
                continue;
            }
            src = file;
            break;
        }
        if (src == null) {
            appendStatus("\nДругой копии monika нет. Нажми «Собрать заново».");
            pushStatusToPage();
            return;
        }
        File parent = dest.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
            appendStatus("\nНе создалась characters: " + parent.getAbsolutePath());
            pushStatusToPage();
            return;
        }
        try {
            long bytes = copyFileToFile(src, dest);
            if (!src.delete()) {
                logLine("recover left source " + src.getAbsolutePath());
            }
            appendStatus("\nВернула Монику: " + src.getAbsolutePath()
                    + " → " + dest.getAbsolutePath() + " (" + bytes + " байт)");
            logLine("recover restore " + src.getAbsolutePath() + " -> " + dest.getAbsolutePath());
        } catch (Exception e) {
            appendStatus("\nНе удалось вернуть файл: " + messageOf(e));
            logLine("recover restore failed " + messageOf(e));
        }
        pushStatusToPage();
    }

    private void recoverMonikaRebuildNow() {
        appendStatus("\nСобираю characters/monika из mbase.");
        testMonikaFileNow(true);
        File dest = charactersMonikaFile();
        if (dest.isFile()) {
            appendStatus("\nФайл на месте. Запусти MAS — стол не должен быть пустым.");
        }
    }

    private File forceMonikaHomeFlag() {
        File root = sideloadDir != null ? sideloadDir : getFilesDir();
        return new File(flagsDir(), ".mas_force_monika_home");
    }

    private void recoverMonikaHomeNow() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        File flag = forceMonikaHomeFlag();
        File parent = flag.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
            appendStatus("\nНе создалась папка Documents: " + parent.getAbsolutePath());
            pushStatusToPage();
            return;
        }
        FileOutputStream out = null;
        try {
            out = new FileOutputStream(flag);
            out.write("home\n".getBytes("UTF-8"));
            out.flush();
            appendStatus("\nФлаг «вернуть за стол» записан: " + flag.getAbsolutePath());
            appendStatus("\nЗапусти MAS — игра снимет «Моника ушла» и покажет её за столом, даже если файл потерян.");
            logLine("recover home flag " + flag.getAbsolutePath());
        } catch (Exception e) {
            appendStatus("\nНе удалось записать флаг: " + messageOf(e));
            logLine("recover home failed " + messageOf(e));
        } finally {
            closeQuietly(out);
        }
        pushStatusToPage();
    }

    private long copyFileToFile(File src, File dest) throws IOException {
        FileInputStream in = null;
        FileOutputStream out = null;
        long total = 0;
        try {
            in = new FileInputStream(src);
            out = new FileOutputStream(dest);
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) >= 0) {
                if (n > 0) {
                    out.write(buf, 0, n);
                    total += n;
                }
            }
            out.flush();
            return total;
        } finally {
            closeQuietly(in);
            closeQuietly(out);
        }
    }

    private void maybeChmodEngine(File dest) {
        String files = getFilesDir().getAbsolutePath();
        String path = dest.getAbsolutePath();
        if (path.startsWith(files)) {
            chmod755(dest);
        }
    }

    private void chmod755(File dest) {
        dest.setReadable(true, false);
        dest.setWritable(true, true);
        dest.setExecutable(true, false);
        try {
            Process chmod = Runtime.getRuntime().exec(new String[] {
                    "chmod", "755", dest.getAbsolutePath()
            });
            chmod.waitFor();
        } catch (Exception e) {
            logLine("chmod 755: " + messageOf(e));
        }
    }

    private void resolvePaths() {
        File documents = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOCUMENTS);
        sideloadDir = new File(documents, "Monika_after_story");
        File mas = new File(sideloadDir, "_mas");
        archivesDir = new File(mas, "archives");
        incomingDir = archivesDir;
        transferDir = new File(sideloadDir, "Transfer");
        gameOverlayDir = new File(sideloadDir, "game");
        logFile = new File(new File(mas, "log"), "launcher.log");
    }

    private File masDir() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        return new File(sideloadDir, "_mas");
    }

    private File flagsDir() {
        return new File(masDir(), "flags");
    }

    private boolean sameFile(File a, File b) {
        if (a == null || b == null) {
            return false;
        }
        return a.getAbsolutePath().equals(b.getAbsolutePath());
    }

    private void ensureLayout() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        if (!canUseDocuments()) {
            return;
        }
        File mas = masDir();
        if (!mas.isDirectory()) {
            mas.mkdirs();
        }
        touchNomedia(mas);
        migrateOldLayout();
        writePathsJson();
    }

    private void migrateOldLayout() {
        File mas = masDir();
        File arch = archivesDir;
        File sm = new File(mas, "submods");
        moveDirContents(new File(sideloadDir, "incoming"), arch);
        File oldArch = new File(sideloadDir, "archives");
        if (!sameFile(oldArch, arch)) {
            moveDirContents(oldArch, arch);
        }
        moveDirContents(new File(sideloadDir, "backups"), backupsDir());
        moveDirContents(new File(sideloadDir, "log"), new File(mas, "log"));
        moveDirContents(new File(sideloadDir, "flags"), flagsDir());
        moveDirContents(new File(sideloadDir, "submods_installed"), new File(sm, "installed"));
        moveDirContents(new File(sideloadDir, "submod_vanilla"), new File(sm, "vanilla"));
        moveDirContents(new File(sideloadDir, "submod_payloads"), new File(sm, "payloads"));
        moveDirContents(new File(sideloadDir, "submod_backups"), new File(sm, "backups"));
        moveDirContents(new File(sideloadDir, "Transfer"), arch);
        File logd = new File(mas, "log");
        moveOneFile(new File(sideloadDir, "launcher.log"), new File(logd, "launcher.log"));
        moveOneFile(new File(sideloadDir, "traceback.txt"), new File(logd, "traceback.txt"));
        moveOneFile(new File(sideloadDir, ".mas_force_monika_home"),
                new File(flagsDir(), ".mas_force_monika_home"));
        moveOneFile(new File(sideloadDir, "mas_os_safe_mode"),
                new File(flagsDir(), "mas_os_safe_mode"));
        deleteIfEmpty(new File(sideloadDir, "incoming"));
        deleteIfEmpty(oldArch);
        deleteIfEmpty(new File(sideloadDir, "backups"));
        deleteIfEmpty(new File(sideloadDir, "log"));
        deleteIfEmpty(new File(sideloadDir, "flags"));
        deleteIfEmpty(new File(sideloadDir, "submods_installed"));
        deleteIfEmpty(new File(sideloadDir, "submod_vanilla"));
        deleteIfEmpty(new File(sideloadDir, "submod_payloads"));
        deleteIfEmpty(new File(sideloadDir, "submod_backups"));
        deleteIfEmpty(new File(sideloadDir, "Transfer"));
    }

    private void moveDirContents(File from, File to) {
        if (from == null || to == null || !from.isDirectory() || sameFile(from, to)) {
            return;
        }
        if (!to.isDirectory() && !to.mkdirs()) {
            logLine("migrate mkdir failed " + to.getAbsolutePath());
            return;
        }
        File[] kids = from.listFiles();
        if (kids == null) {
            return;
        }
        for (int i = 0; i < kids.length; i++) {
            File kid = kids[i];
            if (kid == null) {
                continue;
            }
            File dest = new File(to, kid.getName());
            if (kid.isDirectory()) {
                moveDirContents(kid, dest);
                deleteIfEmpty(kid);
            } else if (kid.isFile()) {
                moveOneFile(kid, dest);
            }
        }
        deleteIfEmpty(from);
    }

    private void moveOneFile(File from, File to) {
        if (from == null || to == null || !from.isFile() || sameFile(from, to)) {
            return;
        }
        File parent = to.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
            return;
        }
        if (to.isFile()) {
            if (!from.delete()) {
                logLine("migrate leftover " + from.getAbsolutePath());
            }
            return;
        }
        if (from.renameTo(to)) {
            logLine("migrate " + from.getName());
            return;
        }
        copyFile(from, to);
        if (to.isFile() && !from.delete()) {
            logLine("migrate copied leftover " + from.getAbsolutePath());
        }
    }

    private void deleteIfEmpty(File dir) {
        if (dir == null || !dir.isDirectory()) {
            return;
        }
        File[] kids = dir.listFiles();
        if (kids != null && kids.length > 0) {
            boolean onlyMeta = true;
            for (int i = 0; i < kids.length; i++) {
                File k = kids[i];
                if (k == null) {
                    continue;
                }
                String n = k.getName();
                if (k.isFile() && (".nomedia".equals(n) || "README.txt".equals(n)
                        || "README_MAS_OS.txt".equals(n))) {
                    continue;
                }
                onlyMeta = false;
                break;
            }
            if (!onlyMeta) {
                return;
            }
            for (int i = 0; i < kids.length; i++) {
                if (kids[i] != null && kids[i].isFile()) {
                    kids[i].delete();
                }
            }
        }
        dir.delete();
    }

    private void writePathsJson() {
        if (sideloadDir == null) {
            return;
        }
        File mas = masDir();
        JSONObject blob = new JSONObject();
        try {
            blob.put("layout", 2);
            blob.put("root", sideloadDir.getAbsolutePath());
            blob.put("saves", savesDir().getAbsolutePath());
            blob.put("characters", new File(sideloadDir, "characters").getAbsolutePath());
            blob.put("custom_bgm", new File(sideloadDir, "custom_bgm").getAbsolutePath());
            blob.put("chess_games", new File(sideloadDir, "chess_games").getAbsolutePath());
            blob.put("piano_songs", new File(sideloadDir, "piano_songs").getAbsolutePath());
            blob.put("game", gameOverlayDir.getAbsolutePath());
            blob.put("system", mas.getAbsolutePath());
            blob.put("archives", archivesDir.getAbsolutePath());
            blob.put("backups", backupsDir().getAbsolutePath());
            blob.put("log", new File(mas, "log").getAbsolutePath());
            blob.put("flags", flagsDir().getAbsolutePath());
            blob.put("submods", new File(mas, "submods").getAbsolutePath());
        } catch (Exception e) {
            logLine("paths json build " + messageOf(e));
            return;
        }
        File out = new File(mas, "paths.json");
        File parent = out.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
            return;
        }
        FileWriter w = null;
        try {
            w = new FileWriter(out);
            w.write(blob.toString(2));
            w.flush();
        } catch (Exception e) {
            logLine("paths json " + messageOf(e));
        } finally {
            if (w != null) {
                try {
                    w.close();
                } catch (Exception ignored) {
                }
            }
        }
        File priv = new File(getFilesDir(), "mas_paths.json");
        FileWriter w2 = null;
        try {
            w2 = new FileWriter(priv);
            w2.write(blob.toString(2));
            w2.flush();
        } catch (Exception ignored) {
        } finally {
            if (w2 != null) {
                try {
                    w2.close();
                } catch (Exception ignored) {
                }
            }
        }
    }

    private boolean needsRuntimePermission() {
        if (Build.VERSION.SDK_INT < 23) {
            return false;
        }
        if (Build.VERSION.SDK_INT >= 30) {
            return false;
        }
        return checkSelfPermission(android.Manifest.permission.WRITE_EXTERNAL_STORAGE)
                != PackageManager.PERMISSION_GRANTED;
    }

    private boolean allFilesAccess() {
        if (Build.VERSION.SDK_INT < 30) {
            return true;
        }
        try {
            return Environment.isExternalStorageManager();
        } catch (Throwable t) {
            return false;
        }
    }

    private boolean canUseDocuments() {
        if (Build.VERSION.SDK_INT >= 30) {
            return allFilesAccess();
        }
        return !needsRuntimePermission();
    }

    private void ensureDocumentsFlag() {
        File priv = getFilesDir();
        if (priv == null) {
            return;
        }
        if (!priv.isDirectory() && !priv.mkdirs()) {
            return;
        }
        writeOneShot(new File(priv, DOCS_FLAG));
        File appFlag = new File(priv, APP_SAVES_FLAG);
        if (appFlag.isFile() && appFlag.delete()) {
            logLine("cleared " + APP_SAVES_FLAG);
        }
    }

    private void showPath() {
        if (pathView != null) {
            pathView.setText(pathReport());
        }
    }

    private void prepareFolders() {
        showPath();
        StringBuilder report = new StringBuilder();
        report.append(pathReport());
        if (!canUseDocuments()) {
            report.append("\nНет доступа ко всем файлам. Documents закрыт, папки не созданы.");
            setStatus(report.toString());
            pushStatusToPage();
            return;
        }
        try {
            ensureLayout();
            File[] needed = userTree();
            boolean allOk = true;
            for (int i = 0; i < needed.length; i++) {
                File dir = needed[i];
                if (dir == null) {
                    continue;
                }
                if (!dir.isDirectory() && !dir.mkdirs()) {
                    allOk = false;
                } else {
                    touchNomedia(dir);
                    writeFolderReadme(dir);
                }
            }
            if (!allOk) {
                report.append("\nПапки: не созданы.");
                setStatus(report.toString());
                pushStatusToPage();
                return;
            }
            foldersPrepared = true;
            report.append("\nПапки: созданы в Documents/Monika_after_story.");
            logLine("folders ready");
            new Thread(new Runnable() {
                @Override
                public void run() {
                    preferApkFonts();
                    installDroppedArchives(true);
                    cleanupAfterUnpack();
                    runHealthReport(true);
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            pushStatusToPage();
                        }
                    });
                }
            }).start();
            if (biosPrepareAttempted) {
                logBiosFiles();
            }
            report.append("\nЛог: ").append(logFile.getAbsolutePath());
        } catch (SecurityException e) {
            report.append("\nНет права создать папки: ").append(messageOf(e));
        } catch (Exception e) {
            report.append("\nНе удалось создать папки: ").append(messageOf(e));
        }
        setStatus(report.toString());
    }

    private String pathReport() {
        String path = sideloadDir == null ? "(нет пути)" : sideloadDir.getAbsolutePath();
        String archives = archivesDir == null ? "(нет пути)" : archivesDir.getAbsolutePath();
        return "Путь: " + path + "\nархивы: " + archives;
    }

    private File[] userTree() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        return new File[] {
                sideloadDir,
                gameOverlayDir,
                savesDir(),
                new File(sideloadDir, "characters"),
                new File(sideloadDir, "custom_bgm"),
                new File(sideloadDir, "chess_games"),
                new File(sideloadDir, "piano_songs"),
                masDir()
        };
    }

    private void touchNomedia(File dir) {
        if (dir == null) {
            return;
        }
        if (!dir.isDirectory() && !dir.mkdirs()) {
            return;
        }
        File nomedia = new File(dir, ".nomedia");
        if (nomedia.isFile()) {
            return;
        }
        FileOutputStream out = null;
        try {
            out = new FileOutputStream(nomedia);
        } catch (Exception ignored) {
        } finally {
            closeQuietly(out);
        }
    }

    private void writeFolderReadme(File dir) {
        if (dir == null || !dir.isDirectory()) {
            return;
        }
        String name = dir.getName();
        String body = null;
        if ("characters".equals(name)) {
            body = "Подарки: файлы .gift, oki doki, imsorry.\n"
                    + "«Взять Монику с собой» пишет сюда файл monika.\n";
        } else if ("custom_bgm".equals(name)) {
            body = "Своя музыка: ogg, opus, mp3.\n"
                    + "Игра подхватит треки в плеере MAS OS.\n";
        } else if ("chess_games".equals(name)) {
            body = "Сохранённые партии шахмат (.pgn).\n";
        } else if ("piano_songs".equals(name)) {
            body = "Свои ноты пианино (.json).\n";
        } else if ("archives".equals(name)) {
            body = "Zip DDLC, .rpa и скачанные паки.\n"
                    + "После распаковки картинки живут в game/.\n";
        } else if ("saves".equals(name)) {
            body = "Сейвы и persistent. Не кладите сюда картинки.\n";
        }
        if (body == null) {
            return;
        }
        File readme = new File(dir, "README.txt");
        if (readme.isFile()) {
            return;
        }
        FileOutputStream out = null;
        try {
            out = new FileOutputStream(readme);
            out.write(body.getBytes("UTF-8"));
        } catch (Exception ignored) {
        } finally {
            closeQuietly(out);
        }
    }

    private boolean isNoNetwork(Throwable error) {
        Throwable cursor = error;
        while (cursor != null) {
            if (cursor instanceof java.net.UnknownHostException) {
                return true;
            }
            if (cursor instanceof java.net.ConnectException) {
                return true;
            }
            String message = cursor.getMessage();
            if (message != null) {
                String lower = message.toLowerCase(Locale.US);
                if (lower.indexOf("unable to resolve host") >= 0) {
                    return true;
                }
                if (lower.indexOf("network is unreachable") >= 0) {
                    return true;
                }
                if (lower.indexOf("no address associated") >= 0) {
                    return true;
                }
            }
            cursor = cursor.getCause();
        }
        return false;
    }

    public class BiosBridge {
        @JavascriptInterface
        public void pickImage() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.pickImage();
                }
            });
        }

        @JavascriptInterface
        public void pickZip() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    pickSubmodArchive();
                }
            });
        }

        @JavascriptInterface
        public void exportSaves() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.exportSaves();
                }
            });
        }

        @JavascriptInterface
        public void importSaves() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.importSaves();
                }
            });
        }

        @JavascriptInterface
        public void shareSaves() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.shareSaves();
                }
            });
        }

        @JavascriptInterface
        public void checkUpdate() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.checkUpdate();
                }
            });
        }

        @JavascriptInterface
        public void downloadUpdate() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.downloadUpdate();
                }
            });
        }

        @JavascriptInterface
        public void installLocalApk() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.installLocalApk();
                }
            });
        }

        @JavascriptInterface
        public void downloadUpdateAgain() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.downloadUpdateAgain();
                }
            });
        }

        @JavascriptInterface
        public void startGame() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.startGame();
                }
            });
        }

        @JavascriptInterface
        public void useNativeUi() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.useNativeUi();
                }
            });
        }

        @JavascriptInterface
        public void useHtmlUi() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.useHtmlUi();
                }
            });
        }

        @JavascriptInterface
        public void startSafe() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    writeFlag("skip_submods");
                    writeSafeModeFlag();
                    startGame();
                }
            });
        }

        @JavascriptInterface
        public void grantAllFiles() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    if (needsRuntimePermission()) {
                        requestPermissions(new String[] {
                                android.Manifest.permission.READ_EXTERNAL_STORAGE,
                                android.Manifest.permission.WRITE_EXTERNAL_STORAGE
                        }, REQ_STORAGE);
                        return;
                    }
                    if (Build.VERSION.SDK_INT >= 30 && !allFilesAccess()) {
                        openAllFilesSettings();
                        return;
                    }
                    ensureDocumentsFlag();
                    prepareFolders();
                    appendStatus("\nДоступ уже есть. Папки Documents готовы.");
                    pushStatusToPage();
                }
            });
        }

        @JavascriptInterface
        public void healthCheck() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    runHealthReport(true);
                    pushStatusToPage();
                }
            });
        }

        @JavascriptInterface
        public void pickFile() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    pickDestKind = "auto";
                    pickAnyFile();
                }
            });
        }

        @JavascriptInterface
        public void pickGift() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    pickDestKind = "gift";
                    pickAnyFile();
                }
            });
        }

        @JavascriptInterface
        public void pickMusic() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    pickDestKind = "music";
                    pickAnyFile();
                }
            });
        }

        @JavascriptInterface
        public void openDocuments() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    openDocumentsNow();
                }
            });
        }

        @JavascriptInterface
        public void diskSnapshot() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    diskSnapshotNow();
                }
            });
        }

        @JavascriptInterface
        public void setBiosView(final String name) {
            String view = "classic";
            if ("island".equals(name) || "deck".equals(name) || "masl".equals(name)) {
                view = name;
            }
            getSharedPreferences("mas_bios", MODE_PRIVATE)
                    .edit()
                    .putString("view", view)
                    .apply();
        }

        @JavascriptInterface
        public void listUrlHistory() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    evalJs("biosUrlHistory", loadUrlHistory().toString());
                }
            });
        }

        @JavascriptInterface
        public void clearUrlHistory() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    getSharedPreferences("mas_bios", MODE_PRIVATE)
                            .edit()
                            .putString("url_history", "[]")
                            .apply();
                    evalJs("biosUrlHistory", "[]");
                    appendStatus("\nИстория ссылок очищена.");
                    pushStatusToPage();
                }
            });
        }

        @JavascriptInterface
        public void removeUrlHistory(final String url) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    dropUrlHistory(url);
                }
            });
        }

        @JavascriptInterface
        public void pickSubmodZip() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    pickSubmodArchive();
                }
            });
        }

        @JavascriptInterface
        public void downloadSubmodUrl(final String url) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    downloadSubmodFromUrl(url);
                }
            });
        }

        @JavascriptInterface
        public void listSubmods() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    appendStatus("\n" + SubmodInstaller.listReport(sideloadDir));
                    evalJs("biosSubmods", SubmodInstaller.listJson(sideloadDir));
                    pushStatusToPage();
                }
            });
        }

        @JavascriptInterface
        public void uninstallLastSubmod() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    uninstallLastSubmodNow();
                }
            });
        }

        @JavascriptInterface
        public void uninstallSubmod(final String id) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    uninstallSubmodNow(id);
                }
            });
        }

        @JavascriptInterface
        public void testMonikaFile() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    testMonikaFileNow(true);
                }
            });
        }

        @JavascriptInterface
        public void checkMonikaFile() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    testMonikaFileNow(false);
                }
            });
        }

        @JavascriptInterface
        public void pickSavesZip() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    pickSavesArchive();
                }
            });
        }

        @JavascriptInterface
        public void pickSavesFolder() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    pickSavesDirectory();
                }
            });
        }

        @JavascriptInterface
        public void installEngine() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    installNativeEngine();
                }
            });
        }

        @JavascriptInterface
        public void testEngine() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    testNativeEngine();
                }
            });
        }

        @JavascriptInterface
        public void testStockfish() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    testStockfishBinary();
                }
            });
        }

        @JavascriptInterface
        public void stockfishReady() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    runStockfishTalk("isready", "readyok", 4000);
                }
            });
        }

        @JavascriptInterface
        public void stockfishGo() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    runStockfishTalk("position startpos\ngo depth 1", "bestmove", 12000);
                }
            });
        }

        @JavascriptInterface
        public void sendStockfish(final String cmd) {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    String line = cmd == null ? "" : cmd.trim();
                    if (line.length() == 0) {
                        appendStatus("\nНапиши UCI-команду в поле.");
                        return;
                    }
                    String wait = "bestmove";
                    int timeout = 12000;
                    String low = line.toLowerCase(Locale.US);
                    if (low.equals("uci") || low.startsWith("uci\n")) {
                        wait = "uciok";
                        timeout = 4000;
                    } else if (low.indexOf("isready") >= 0) {
                        wait = "readyok";
                        timeout = 4000;
                    } else if (low.indexOf("go ") >= 0 || low.equals("go")) {
                        wait = "bestmove";
                        timeout = 15000;
                    } else {
                        wait = null;
                        timeout = 2500;
                    }
                    runStockfishTalk(line, wait, timeout);
                }
            });
        }

        @JavascriptInterface
        public void toggleBoot() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    toggleBootFlag();
                }
            });
        }

        @JavascriptInterface
        public void shareLogs() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    shareLauncherLog();
                }
            });
        }

        @JavascriptInterface
        public void downloadArchives() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.downloadArchives();
                }
            });
        }

        @JavascriptInterface
        public void downloadDdlcMoe() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.downloadDdlcMoe();
                }
            });
        }

        @JavascriptInterface
        public void installArchives() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    new Thread(new Runnable() {
                        @Override
                        public void run() {
                            installDroppedArchives(false);
                            runOnUiThread(new Runnable() {
                                @Override
                                public void run() {
                                    pushStatusToPage();
                                }
                            });
                        }
                    }).start();
                }
            });
        }

        @JavascriptInterface
        public void pickArchive() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.pickArchive();
                }
            });
        }

        @JavascriptInterface
        public void checkArchives() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    reportArchiveStatus();
                    pushStatusToPage();
                }
            });
        }

        @JavascriptInterface
        public void showTraceback() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    LauncherActivity.this.showTraceback();
                }
            });
        }

        @JavascriptInterface
        public void pauseDownload() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    pauseDownloadNow();
                }
            });
        }

        @JavascriptInterface
        public void resumeDownload() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    resumeDownloadNow();
                }
            });
        }

        @JavascriptInterface
        public void cancelDownload() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    cancelDownloadNow();
                }
            });
        }

        @JavascriptInterface
        public void recoverMonikaScan() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    recoverMonikaScanNow();
                }
            });
        }

        @JavascriptInterface
        public void recoverMonikaRestore() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    recoverMonikaRestoreNow();
                }
            });
        }

        @JavascriptInterface
        public void recoverMonikaRebuild() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    recoverMonikaRebuildNow();
                }
            });
        }

        @JavascriptInterface
        public void recoverMonikaHome() {
            runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    recoverMonikaHomeNow();
                }
            });
        }
    }

    private boolean downloadUrlToFile(String url, File dest, String expectedHash) {
        return downloadUrlToFile(url, dest, expectedHash, false);
    }

    private boolean downloadUrlToFile(String url, File dest, String expectedHash, boolean requireZip) {
        File part = new File(dest.getAbsolutePath() + ".part");
        lastDownloadUrl = url;
        lastDownloadDest = dest;
        lastDownloadHash = expectedHash;
        lastDownloadRequireZip = requireZip;
        if (downloadPaused) {
            pushDlState("paused");
        } else {
            pushDlState("running");
        }
        boolean renamed = false;
        try {
            File parent = dest.getParentFile();
            if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
                postStatus("\nНет папки для " + dest.getName());
                return false;
            }
            resetProgress();
            long started = System.currentTimeMillis();
            long lastUi = 0;
            int lastLoggedPct = -10;
            while (!downloadCancel) {
                while (downloadPaused && !downloadCancel) {
                    pushDlState("paused");
                    try {
                        Thread.sleep(250);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        return false;
                    }
                }
                if (downloadCancel) {
                    break;
                }
                pushDlState("running");
                HttpURLConnection conn = null;
                InputStream in = null;
                FileOutputStream out = null;
                boolean eof = false;
                try {
                    long got = part.isFile() ? part.length() : 0L;
                    if (got > 0) {
                        postStatus("\nдокачка с " + got + " байт");
                    }
                    conn = openGet(url, got);
                    int code = conn.getResponseCode();
                    if (got > 0 && code == HttpURLConnection.HTTP_OK) {
                        postStatus("\nсервер не умеет докачку, начинаю сначала");
                        conn.disconnect();
                        conn = null;
                        if (part.exists() && !part.delete()) {
                            postStatus("\nне удалось сбросить .part");
                            return false;
                        }
                        continue;
                    }
                    if (code != HttpURLConnection.HTTP_OK && code != 206) {
                        postStatus("\nСервер ответил " + code);
                        return false;
                    }
                    String type = conn.getContentType();
                    if (requireZip && type != null && type.toLowerCase(Locale.US).indexOf("html") >= 0) {
                        postStatus("\nСервер отдал HTML, не zip.");
                        return false;
                    }
                    got = part.isFile() ? part.length() : 0L;
                    long total = parseTotalLength(conn, got);
                    in = conn.getInputStream();
                    out = new FileOutputStream(part, got > 0);
                    byte[] buf = new byte[8192];
                    int n;
                    while ((n = in.read(buf)) >= 0) {
                        if (downloadCancel || downloadPaused) {
                            break;
                        }
                        if (n <= 0) {
                            continue;
                        }
                        out.write(buf, 0, n);
                        got += n;
                        long now = System.currentTimeMillis();
                        double speed = got / Math.max(0.001, (now - started) / 1000.0);
                        int pct = total > 0 ? (int) ((got * 100L) / total) : -1;
                        if (now - lastUi >= 200 || pct == 100) {
                            lastUi = now;
                            showProgress(got, total, speed);
                        }
                        if (pct >= 0 && pct / 10 != lastLoggedPct / 10) {
                            lastLoggedPct = pct;
                            postStatus("\n" + progressText(got, total, speed));
                        } else if (pct < 0 && got == n) {
                            postStatus("\n" + progressText(got, total, speed));
                        }
                    }
                    out.flush();
                    if (downloadCancel) {
                        postStatus("\nскачивание отменено");
                        return false;
                    }
                    if (downloadPaused) {
                        postStatus("\nпауза на " + got + " байт. Включи VPN и нажми Продолжить.");
                    } else {
                        double speed = got / Math.max(0.001, (System.currentTimeMillis() - started) / 1000.0);
                        showProgress(got, total > 0 ? total : got, speed);
                        postStatus("\n" + progressText(got, total > 0 ? total : got, speed));
                        eof = true;
                    }
                } catch (Exception e) {
                    if (downloadCancel) {
                        return false;
                    }
                    if (isNoNetwork(e)) {
                        postStatus("\nнет сети — пауза. Включи VPN и нажми Продолжить.");
                        logLine("no network, paused");
                    } else {
                        postStatus("\nобрыв: " + messageOf(e) + " — пауза. Продолжить, когда сеть появится.");
                        logLine("download pause " + messageOf(e));
                    }
                    downloadPaused = true;
                    pushDlState("paused");
                } finally {
                    if (in != null) {
                        try {
                            in.close();
                        } catch (IOException ignored) {
                        }
                    }
                    if (out != null) {
                        try {
                            out.close();
                        } catch (IOException ignored) {
                        }
                    }
                    if (conn != null) {
                        conn.disconnect();
                    }
                }
                if (eof) {
                    if (dest.exists() && !dest.delete()) {
                        postStatus("\nНе удалось заменить " + dest.getName());
                        return false;
                    }
                    if (!part.renameTo(dest)) {
                        postStatus("\nНе удалось записать " + dest.getName());
                        return false;
                    }
                    renamed = true;
                    if (requireZip && !isZipFile(dest)) {
                        postStatus("\n" + dest.getName() + " не zip.");
                        dest.delete();
                        return false;
                    }
                    pushDlState("idle");
                    return acceptHash(dest, expectedHash);
                }
            }
            postStatus("\nскачивание отменено");
            return false;
        } catch (Exception e) {
            postStatus("\nСкачивание не удалось: " + messageOf(e));
            logLine("download failed " + messageOf(e));
            return false;
        } finally {
            if (!renamed && part.exists() && downloadCancel) {
                part.delete();
            }
            if (downloadCancel) {
                downloadPaused = false;
                pushDlState("idle");
            } else if (downloadPaused) {
                pushDlState("paused");
            }
        }
    }

    private long parseTotalLength(HttpURLConnection conn, long already) {
        String cr = conn.getHeaderField("Content-Range");
        if (cr != null) {
            int slash = cr.lastIndexOf('/');
            if (slash >= 0 && slash + 1 < cr.length()) {
                try {
                    long total = Long.parseLong(cr.substring(slash + 1).trim());
                    if (total > 0) {
                        return total;
                    }
                } catch (Exception ignored) {
                }
            }
        }
        long rem = contentLength(conn);
        if (rem > 0) {
            return already + rem;
        }
        return -1L;
    }

    private void pushDlState(final String state) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                evalJs("biosDlState", state);
            }
        });
    }

    private HttpURLConnection openGet(String url) throws IOException {
        return openGet(url, 0L);
    }

    private HttpURLConnection openGet(String url, long rangeFrom) throws IOException {
        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setInstanceFollowRedirects(true);
        conn.setConnectTimeout(20000);
        conn.setReadTimeout(60000);
        conn.setRequestProperty("User-Agent", "MAS-BIOS/1.0");
        if (rangeFrom > 0) {
            conn.setRequestProperty("Range", "bytes=" + rangeFrom + "-");
        }
        conn.connect();
        return conn;
    }

    private long contentLength(HttpURLConnection conn) {
        if (Build.VERSION.SDK_INT >= 24) {
            long len = conn.getContentLengthLong();
            return len > 0 ? len : -1L;
        }
        int len = conn.getContentLength();
        return len > 0 ? len : -1L;
    }

    private String fetchOptionalSha(String url) {
        HttpURLConnection conn = null;
        try {
            conn = openGet(url);
            if (conn.getResponseCode() != HttpURLConnection.HTTP_OK) {
                return null;
            }
            InputStream in = conn.getInputStream();
            byte[] buf = new byte[256];
            int n = in.read(buf);
            in.close();
            if (n <= 0) {
                return null;
            }
            return normalizeHash(new String(buf, 0, n, "UTF-8"));
        } catch (Exception e) {
            return null;
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }

    private String normalizeHash(String raw) {
        if (raw == null) {
            return null;
        }
        String line = raw.trim().toLowerCase(Locale.US);
        int nl = line.indexOf('\n');
        if (nl >= 0) {
            line = line.substring(0, nl).trim();
        }
        if (line.startsWith("sha256:")) {
            line = line.substring("sha256:".length()).trim();
        }
        int space = line.indexOf(' ');
        if (space > 0) {
            line = line.substring(0, space);
        }
        if (line.length() != 64) {
            return null;
        }
        return line;
    }

    private boolean acceptHash(File file, String expectedHash) {
        String expected = normalizeHash(expectedHash);
        if (expected == null) {
            postStatus("\nхеш не задан, пропуск");
            logLine("hash skipped " + file.getName());
            return true;
        }
        try {
            String actual = sha256(file);
            if (expected.equals(actual)) {
                postStatus("\nхеш совпал");
                logLine("hash ok " + file.getName());
                return true;
            }
            postStatus("\nфайл битый, качни снова");
            logLine("hash mismatch " + file.getName());
            file.delete();
            return false;
        } catch (Exception e) {
            postStatus("\nНе удалось посчитать хеш: " + messageOf(e));
            logLine("hash error " + messageOf(e));
            file.delete();
            return false;
        }
    }

    private String sha256(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        FileInputStream in = new FileInputStream(file);
        try {
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) >= 0) {
                if (n > 0) {
                    digest.update(buf, 0, n);
                }
            }
        } finally {
            in.close();
        }
        byte[] raw = digest.digest();
        StringBuilder hex = new StringBuilder();
        for (int i = 0; i < raw.length; i++) {
            hex.append(String.format(Locale.US, "%02x", raw[i] & 0xff));
        }
        return hex.toString();
    }

    private void resetProgress() {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (progressBar != null) {
                    progressBar.setIndeterminate(false);
                    progressBar.setMax(100);
                    progressBar.setProgress(0);
                }
                if (progressLine != null) {
                    progressLine.setText("");
                }
            }
        });
    }

    private void showProgress(final long got, final long total, final double bytesPerSec) {
        final String line = progressText(got, total, bytesPerSec);
        final int pct = total > 0 ? (int) ((got * 100L) / total) : -1;
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (progressLine != null) {
                    progressLine.setText(line);
                }
                if (progressBar != null) {
                    if (pct >= 0) {
                        progressBar.setIndeterminate(false);
                        progressBar.setMax(100);
                        progressBar.setProgress(pct > 100 ? 100 : pct);
                    } else {
                        progressBar.setIndeterminate(true);
                    }
                }
                pushWebProgress(line, pct);
            }
        });
    }

    private void pushWebProgress(final String line, final int pct) {
        if (webView == null || !pageReady) {
            return;
        }
        final String js = "if(window.biosProgress){window.biosProgress(" + jsString(line) + "," + pct + ");}";
        webView.post(new Runnable() {
            @Override
            public void run() {
                if (webView == null) {
                    return;
                }
                webView.evaluateJavascript(js, null);
            }
        });
    }

    private String progressText(long got, long total, double bytesPerSec) {
        String speed = formatSpeed(bytesPerSec);
        String gotS = formatSize(got);
        if (total > 0) {
            int pct = (int) ((got * 100L) / total);
            if (pct > 100) {
                pct = 100;
            }
            String eta = "";
            long left = total - got;
            if (bytesPerSec > 1 && left > 0) {
                eta = "  осталось " + formatEta((long) (left / bytesPerSec));
            }
            return "скачано " + gotS + " / " + formatSize(total) + "  " + pct + "%  " + speed + eta;
        }
        return "скачано " + gotS + "  " + speed;
    }

    private String formatSize(long bytes) {
        if (bytes < 0) {
            bytes = 0;
        }
        double mb = bytes / (1024.0 * 1024.0);
        if (mb >= 10) {
            return String.format(Locale.US, "%.0f МБ", mb);
        }
        if (bytes >= 1024 * 1024) {
            return String.format(Locale.US, "%.1f МБ", mb);
        }
        if (bytes >= 1024) {
            return String.format(Locale.US, "%.0f КБ", bytes / 1024.0);
        }
        return bytes + " Б";
    }

    private String formatEta(long seconds) {
        if (seconds < 0) {
            seconds = 0;
        }
        if (seconds < 60) {
            return seconds + " с";
        }
        long m = seconds / 60;
        long s = seconds % 60;
        if (m < 60) {
            return m + " мин " + s + " с";
        }
        long h = m / 60;
        m = m % 60;
        return h + " ч " + m + " мин";
    }

    private String formatSpeed(double bytesPerSec) {
        if (bytesPerSec >= 1024.0 * 1024.0) {
            return String.format(Locale.US, "%.1f МБ/с", bytesPerSec / (1024.0 * 1024.0));
        }
        return String.format(Locale.US, "%.0f КБ/с", bytesPerSec / 1024.0);
    }

    private void postStatus(final String line) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                appendStatus(line);
            }
        });
    }

    private void unzipIntoSideload(File zip) {
        File dest = unzipDestination(zip);
        int written = unzipReplace(zip, dest);
        appendStatus("\nУстановлен " + zip.getName() + " → " + dest.getAbsolutePath() + ", файлов: " + written);
        logLine("installed " + zip.getName() + " into " + dest.getAbsolutePath() + " files " + written);
    }

    private File unzipDestination(File zip) {
        if (zipHasPrefix(zip, "game/")) {
            return sideloadDir;
        }
        return gameOverlayDir != null ? gameOverlayDir : sideloadDir;
    }

    private boolean zipHasPrefix(File zip, String prefix) {
        ZipFile zipFile = null;
        try {
            zipFile = new ZipFile(zip);
            Enumeration<? extends ZipEntry> entries = zipFile.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                if (name == null) {
                    continue;
                }
                String relative = name.replace('\\', '/');
                if (relative.startsWith(prefix)) {
                    return true;
                }
            }
        } catch (Exception ignored) {
        } finally {
            if (zipFile != null) {
                try {
                    zipFile.close();
                } catch (IOException ignored) {
                }
            }
        }
        return false;
    }

    private void copyEntry(ZipFile zipFile, ZipEntry entry, File out) throws IOException {
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
                } catch (IOException ignored) {
                }
            }
            if (outs != null) {
                try {
                    outs.close();
                } catch (IOException ignored) {
                }
            }
        }
    }

    private boolean forbiddenZipName(String name) {
        if (name == null || name.length() == 0) {
            return true;
        }
        String norm = name.replace('\\', '/');
        if (norm.startsWith("/")) {
            return true;
        }
        return norm.indexOf("..") >= 0;
    }

    private boolean staysInside(File root, File candidate) {
        try {
            String base = root.getCanonicalPath();
            String target = candidate.getCanonicalPath();
            return target.equals(base) || target.startsWith(base + File.separator);
        } catch (IOException e) {
            return false;
        }
    }

    private File savesDir() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        return new File(sideloadDir, "saves");
    }

    private File backupsDir() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        return new File(masDir(), "backups");
    }

    private void exportSaves() {
        File saves = savesDir();
        File backups = backupsDir();
        if (!saves.isDirectory()) {
            appendStatus("\nЭкспорт: папки saves нет.");
            logLine("export saves missing");
            return;
        }
        if (!backups.isDirectory() && !backups.mkdirs()) {
            appendStatus("\nЭкспорт: не создана папка backups.");
            logLine("export backups failed");
            return;
        }
        String stamp = new SimpleDateFormat("yyyyMMdd_HHmm", Locale.US).format(new Date());
        File zip = new File(backups, "saves_" + stamp + ".zip");
        ZipOutputStream zos = null;
        int count = 0;
        try {
            zos = new ZipOutputStream(new FileOutputStream(zip));
            count = addTreeToZip(zos, saves, "");
            zos.finish();
            appendStatus("\nЭкспорт " + zip.getAbsolutePath() + ", файлов: " + count);
            logLine("export " + zip.getAbsolutePath() + " files " + count);
        } catch (Exception e) {
            appendStatus("\nЭкспорт не удался: " + messageOf(e));
            logLine("export failed " + messageOf(e));
        } finally {
            if (zos != null) {
                try {
                    zos.close();
                } catch (IOException ignored) {
                }
            }
        }
    }

    private int addTreeToZip(ZipOutputStream zos, File dir, String prefix) throws IOException {
        File[] files = dir.listFiles();
        if (files == null) {
            return 0;
        }
        int count = 0;
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null) {
                continue;
            }
            String name = file.getName();
            if (name == null || name.indexOf("..") >= 0) {
                continue;
            }
            String entryName = prefix.length() == 0 ? name : prefix + "/" + name;
            if (file.isDirectory()) {
                count += addTreeToZip(zos, file, entryName);
            } else if (file.isFile()) {
                ZipEntry entry = new ZipEntry(entryName);
                zos.putNextEntry(entry);
                copyFileToStream(file, zos);
                zos.closeEntry();
                count++;
            }
        }
        return count;
    }

    private void copyFileToStream(File file, ZipOutputStream zos) throws IOException {
        InputStream in = null;
        try {
            in = new java.io.FileInputStream(file);
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) >= 0) {
                if (n > 0) {
                    zos.write(buf, 0, n);
                }
            }
        } finally {
            if (in != null) {
                in.close();
            }
        }
    }

    private void pickImage() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("image/*");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivityForResult(intent, REQ_PICK_IMAGE);
        } catch (Exception e) {
            appendStatus("\nПикер картинок не открылся: " + messageOf(e));
            logLine("pick image failed " + messageOf(e));
        }
    }

    private void pickZip() {
        pickSubmodArchive();
    }

    private void pickSubmodArchive() {
        if (!canUseDocuments()) {
            appendStatus("\nНет доступа ко всем файлам.");
            pushStatusToPage();
            return;
        }
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[] {
                "application/zip",
                "application/x-zip-compressed",
                "*/*"
        });
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivityForResult(intent, REQ_PICK_SUBMOD);
        } catch (Exception e) {
            appendStatus("\nПикер сабмода не открылся: " + messageOf(e));
        }
    }

    private void pickSavesArchive() {
        if (!canUseDocuments()) {
            appendStatus("\nНет доступа ко всем файлам.");
            pushStatusToPage();
            return;
        }
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.putExtra(Intent.EXTRA_MIME_TYPES, new String[] {
                "application/zip",
                "application/x-zip-compressed",
                "*/*"
        });
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivityForResult(intent, REQ_PICK_SAVES_ZIP);
        } catch (Exception e) {
            appendStatus("\nПикер zip сейвов не открылся: " + messageOf(e));
        }
    }

    private void pickSavesDirectory() {
        if (!canUseDocuments()) {
            appendStatus("\nНет доступа ко всем файлам.");
            pushStatusToPage();
            return;
        }
        if (Build.VERSION.SDK_INT < 21) {
            appendStatus("\nВыбор папки нужен Android 5+. Положи zip и импортируй архивом.");
            return;
        }
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION
                | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
        try {
            startActivityForResult(intent, REQ_PICK_SAVES_DIR);
        } catch (Exception e) {
            appendStatus("\nПикер папки не открылся: " + messageOf(e));
        }
    }

    private void downloadSubmodFromUrl(String raw) {
        if (!canUseDocuments()) {
            appendStatus("\nНет доступа ко всем файлам.");
            pushStatusToPage();
            return;
        }
        String url = raw == null ? "" : raw.trim();
        if (url.length() == 0) {
            promptSubmodUrl();
            return;
        }
        startSubmodDownload(url);
    }

    private void promptSubmodUrl() {
        final EditText input = new EditText(this);
        input.setHint("https://github.com/user/repo");
        input.setSingleLine(true);
        AlertDialog.Builder box = new AlertDialog.Builder(this);
        box.setTitle("Ссылка на zip сабмода");
        box.setView(input);
        box.setPositiveButton("Скачать", new DialogInterface.OnClickListener() {
            @Override
            public void onClick(DialogInterface dialog, int which) {
                startSubmodDownload(input.getText() == null ? "" : input.getText().toString());
            }
        });
        box.setNegativeButton("Отмена", null);
        box.show();
    }

    private void startSubmodDownload(String raw) {
        final String url = SubmodInstaller.rewriteGithubUrl(raw);
        if (url.length() == 0 || !(url.startsWith("http://") || url.startsWith("https://"))) {
            appendStatus("\nНужна http(s) ссылка на zip или репозиторий GitHub.");
            return;
        }
        rememberUrl(raw == null ? url : raw.trim());
        if (downloadRunning) {
            appendStatus("\nУже идёт загрузка.");
            return;
        }
        if (incomingDir == null || (!incomingDir.isDirectory() && !incomingDir.mkdirs())) {
            appendStatus("\nНет папки архивов.");
            return;
        }
        downloadCancel = false;
        downloadPaused = false;
        downloadRunning = true;
        appendStatus("\nКачаю сабмод: " + url);
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    File dest = new File(incomingDir, "submod_download.zip");
                    String tryUrl = url;
                    boolean ok = downloadUrlToFile(tryUrl, dest, null, true);
                    if (!ok && !downloadCancel && tryUrl.endsWith("/main.zip")) {
                        tryUrl = tryUrl.substring(0, tryUrl.length() - "/main.zip".length()) + "/master.zip";
                        postStatus("\nmain.zip нет, пробую master.zip");
                        ok = downloadUrlToFile(tryUrl, dest, null, true);
                    }
                    if (!ok) {
                        postStatus("\nСабмод не скачался.");
                        return;
                    }
                    installSubmodFile(dest);
                } finally {
                    downloadRunning = false;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            pushStatusToPage();
                        }
                    });
                }
            }
        }).start();
    }

    private void copyPickedSubmod(Uri uri) {
        if (incomingDir == null) {
            resolvePaths();
        }
        if (!incomingDir.isDirectory() && !incomingDir.mkdirs()) {
            appendStatus("\nПапка архивов не создана.");
            return;
        }
        String name = displayName(uri);
        if (name == null || name.length() == 0) {
            name = "submod.zip";
        }
        File dest = new File(incomingDir, safeFileName(name));
        try {
            copyUriToFile(uri, dest);
            appendStatus("\nzip сабмода: " + dest.getName());
        } catch (Exception e) {
            appendStatus("\nСабмод не скопировался: " + messageOf(e));
            return;
        }
        final File zip = dest;
        if (downloadRunning) {
            appendStatus("\nУже идёт работа с файлами.");
            return;
        }
        downloadRunning = true;
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    installSubmodFile(zip);
                } finally {
                    downloadRunning = false;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            pushStatusToPage();
                        }
                    });
                }
            }
        }).start();
    }

    private void installSubmodFile(File zip) {
        SubmodInstaller.Result result = SubmodInstaller.install(zip, gameOverlayDir, sideloadDir);
        postStatus("\n" + result.message);
        logLine("submod " + result.message);
        evalJs("biosSubmods", SubmodInstaller.listJson(sideloadDir));
    }

    private void uninstallLastSubmodNow() {
        uninstallSubmodNow(SubmodInstaller.lastId(sideloadDir));
    }

    private void uninstallSubmodNow(final String id) {
        if (id == null || id.length() == 0) {
            appendStatus("\nСтавить было нечего: манифестов нет.");
            return;
        }
        if (downloadRunning) {
            appendStatus("\nУже идёт работа с файлами.");
            return;
        }
        downloadRunning = true;
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    SubmodInstaller.Result result = SubmodInstaller.uninstall(
                            id, gameOverlayDir, sideloadDir);
                    postStatus("\n" + result.message);
                    logLine("submod uninstall " + result.message);
                    evalJs("biosSubmods", SubmodInstaller.listJson(sideloadDir));
                } finally {
                    downloadRunning = false;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            pushStatusToPage();
                        }
                    });
                }
            }
        }).start();
    }

    private String safeFileName(String name) {
        String n = name.replace('\\', '/');
        int slash = n.lastIndexOf('/');
        if (slash >= 0) {
            n = n.substring(slash + 1);
        }
        n = n.replaceAll("[^A-Za-z0-9._-]+", "_");
        if (n.length() == 0) {
            n = "picked.zip";
        }
        return n;
    }

    private void importPickedSavesZip(final Uri uri) {
        if (incomingDir == null) {
            resolvePaths();
        }
        if (!incomingDir.isDirectory() && !incomingDir.mkdirs()) {
            appendStatus("\nПапка архивов не создана.");
            return;
        }
        if (downloadRunning) {
            appendStatus("\nУже идёт работа с файлами.");
            return;
        }
        downloadRunning = true;
        appendStatus("\nКопирую zip сейвов…");
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    File dest = new File(incomingDir, "saves_import.zip");
                    copyUriToFile(uri, dest);
                    int count = importSavesPayload(dest);
                    postStatus("\nИмпорт zip: файлов " + count
                            + " → Documents/Monika_after_story");
                    logLine("import zip files " + count);
                } catch (Exception e) {
                    postStatus("\nИмпорт zip не удался: " + messageOf(e));
                } finally {
                    downloadRunning = false;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            pushStatusToPage();
                        }
                    });
                }
            }
        }).start();
    }

    private void importPickedSavesFolder(final Uri tree) {
        if (Build.VERSION.SDK_INT < 21) {
            appendStatus("\nВыбор папки нужен Android 5+.");
            return;
        }
        try {
            getContentResolver().takePersistableUriPermission(
                    tree, Intent.FLAG_GRANT_READ_URI_PERMISSION);
        } catch (Exception ignored) {
        }
        if (downloadRunning) {
            appendStatus("\nУже идёт работа с файлами.");
            return;
        }
        downloadRunning = true;
        appendStatus("\nЧитаю папку сейвов…");
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    int count = importSavesTree(tree);
                    postStatus("\nИмпорт папки: файлов " + count
                            + " → Documents/Monika_after_story (saves, characters, …)");
                    logLine("import tree files " + count);
                } catch (Exception e) {
                    postStatus("\nИмпорт папки не удался: " + messageOf(e));
                } finally {
                    downloadRunning = false;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            pushStatusToPage();
                        }
                    });
                }
            }
        }).start();
    }

    private int importSavesPayload(File zip) {
        ZipFile zipFile = null;
        int count = 0;
        try {
            zipFile = new ZipFile(zip);
            Enumeration<? extends ZipEntry> entries = zipFile.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (entry == null || entry.isDirectory()) {
                    continue;
                }
                String name = entry.getName();
                if (forbiddenZipName(name)) {
                    continue;
                }
                File dest = destForImportedPath(name.replace('\\', '/'));
                if (dest == null) {
                    continue;
                }
                File parent = dest.getParentFile();
                if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
                    continue;
                }
                copyEntry(zipFile, entry, dest);
                count++;
            }
        } catch (Exception e) {
            postStatus("\nРазбор zip сейвов: " + messageOf(e));
        } finally {
            if (zipFile != null) {
                try {
                    zipFile.close();
                } catch (Exception ignored) {
                }
            }
        }
        return count;
    }

    private int importSavesTree(Uri tree) {
        if (Build.VERSION.SDK_INT < 21) {
            return 0;
        }
        String docId = DocumentsContract.getTreeDocumentId(tree);
        return walkImportTree(tree, docId, "");
    }

    private int walkImportTree(Uri tree, String docId, String relative) {
        int count = 0;
        Uri children = DocumentsContract.buildChildDocumentsUriUsingTree(tree, docId);
        Cursor cursor = null;
        try {
            cursor = getContentResolver().query(
                    children,
                    new String[] {
                            DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                            DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                            DocumentsContract.Document.COLUMN_MIME_TYPE
                    },
                    null, null, null);
            if (cursor == null) {
                return 0;
            }
            while (cursor.moveToNext()) {
                String childId = cursor.getString(0);
                String name = cursor.getString(1);
                String mime = cursor.getString(2);
                if (name == null || name.length() == 0) {
                    continue;
                }
                String childRel = relative.length() == 0 ? name : relative + "/" + name;
                if (DocumentsContract.Document.MIME_TYPE_DIR.equals(mime)) {
                    count += walkImportTree(tree, childId, childRel);
                    continue;
                }
                File dest = destForImportedPath(childRel);
                if (dest == null) {
                    continue;
                }
                File parent = dest.getParentFile();
                if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
                    continue;
                }
                Uri childUri = DocumentsContract.buildDocumentUriUsingTree(tree, childId);
                InputStream in = null;
                try {
                    in = getContentResolver().openInputStream(childUri);
                    if (in != null && writeStream(in, dest)) {
                        count++;
                    }
                } catch (Exception ignored) {
                } finally {
                    closeQuietly(in);
                }
            }
        } catch (Exception e) {
            postStatus("\nОбход папки: " + messageOf(e));
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
        return count;
    }

    private File destForImportedPath(String relative) {
        if (relative == null) {
            return null;
        }
        String r = relative.replace('\\', '/');
        while (r.startsWith("/")) {
            r = r.substring(1);
        }
        if (r.length() == 0 || r.endsWith("/")) {
            return null;
        }
        String low = r.toLowerCase(Locale.US);
        if (low.contains("__macosx/") || low.endsWith(".ds_store")) {
            return null;
        }
        String mapped = stripKnownFolder(r, "saves/");
        if (mapped != null) {
            return new File(savesDir(), mapped);
        }
        mapped = stripKnownFolder(r, "characters/");
        if (mapped != null) {
            return new File(new File(sideloadDir, "characters"), mapped);
        }
        mapped = stripKnownFolder(r, "custom_bgm/");
        if (mapped != null) {
            return new File(new File(sideloadDir, "custom_bgm"), mapped);
        }
        mapped = stripKnownFolder(r, "chess_games/");
        if (mapped != null) {
            return new File(new File(sideloadDir, "chess_games"), mapped);
        }
        mapped = stripKnownFolder(r, "piano_songs/");
        if (mapped != null) {
            return new File(new File(sideloadDir, "piano_songs"), mapped);
        }
        String base = r;
        int slash = r.lastIndexOf('/');
        if (slash >= 0) {
            base = r.substring(slash + 1);
        }
        String blow = base.toLowerCase(Locale.US);
        if (blow.equals("persistent") || blow.startsWith("persistent-")
                || blow.startsWith("auto-") || blow.endsWith(".save")
                || blow.equals("persistent.bak")) {
            return new File(savesDir(), base);
        }
        if (blow.endsWith(".gift") || blow.equals("oki doki") || blow.equals("imsorry")
                || blow.equals("imsorry.txt") || blow.equals("monika") || blow.equals("monika.chr")) {
            return new File(new File(sideloadDir, "characters"), base);
        }
        if (blow.endsWith(".ogg") || blow.endsWith(".opus") || blow.endsWith(".mp3")) {
            return new File(new File(sideloadDir, "custom_bgm"), base);
        }
        return null;
    }

    private String stripKnownFolder(String relative, String folder) {
        String low = relative.toLowerCase(Locale.US);
        String f = folder.toLowerCase(Locale.US);
        int idx = low.indexOf("/" + f);
        if (idx >= 0) {
            return relative.substring(idx + 1 + folder.length());
        }
        if (low.startsWith(f)) {
            return relative.substring(folder.length());
        }
        return null;
    }

    private String biosViewName() {
        try {
            SharedPreferences prefs = getSharedPreferences("mas_bios", MODE_PRIVATE);
            String view = prefs.getString("view", "classic");
            if ("island".equals(view) || "deck".equals(view) || "masl".equals(view)) {
                return view;
            }
        } catch (Exception ignored) {
        }
        return "classic";
    }

    private void pickAnyFile() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.setType("*/*");
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try {
            startActivityForResult(intent, REQ_PICK_FILE);
        } catch (Exception e) {
            appendStatus("\nПикер файла не открылся: " + messageOf(e));
            logLine("pick file failed " + messageOf(e));
        }
    }

    private File destForPickedName(String name) {
        if (sideloadDir == null) {
            resolvePaths();
        }
        String low = name == null ? "" : name.toLowerCase(Locale.US);
        String kind = pickDestKind == null ? "auto" : pickDestKind;
        if ("gift".equals(kind)) {
            return new File(new File(sideloadDir, "characters"), name);
        }
        if ("music".equals(kind)) {
            return new File(new File(sideloadDir, "custom_bgm"), name);
        }
        if (low.endsWith(".gift") || low.equals("oki doki") || low.equals("imsorry")
                || low.equals("imsorry.txt")) {
            return new File(new File(sideloadDir, "characters"), name);
        }
        if (low.endsWith(".ogg") || low.endsWith(".opus") || low.endsWith(".mp3")
                || low.endsWith(".wav") || low.endsWith(".flac")) {
            return new File(new File(sideloadDir, "custom_bgm"), name);
        }
        if (low.endsWith(".pgn")) {
            return new File(new File(sideloadDir, "chess_games"), name);
        }
        if (low.endsWith(".json")) {
            return new File(new File(sideloadDir, "piano_songs"), name);
        }
        if (low.endsWith(".rpa")) {
            return new File(archivesDir, name);
        }
        if (archivesDir == null) {
            archivesDir = new File(masDir(), "archives");
            incomingDir = archivesDir;
        }
        return new File(archivesDir, name);
    }

    private void copyPickedFile(Uri uri) {
        if (sideloadDir == null) {
            resolvePaths();
        }
        String name = displayName(uri);
        if (name == null || name.length() == 0) {
            name = "picked.bin";
        }
        name = name.replace('\\', '/');
        int slash = name.lastIndexOf('/');
        if (slash >= 0) {
            name = name.substring(slash + 1);
        }
        File dest = destForPickedName(name);
        File parent = dest.getParentFile();
        if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
            appendStatus("\nНе создалась папка " + parent.getAbsolutePath());
            logLine("pick dest mkdir failed " + parent.getAbsolutePath());
            pickDestKind = "auto";
            return;
        }
        try {
            long bytes = copyUriToFile(uri, dest);
            String folder = parent == null ? "?" : parent.getName();
            appendStatus("\nФайл «" + name + "» → " + folder + "/" + dest.getName()
                    + " (" + bytes + " байт)\n" + dest.getAbsolutePath());
            logLine("picked file " + name + " -> " + dest.getAbsolutePath()
                    + " bytes " + bytes + " kind=" + pickDestKind);
        } catch (Exception e) {
            appendStatus("\nФайл не скопирован: " + messageOf(e));
            logLine("picked file failed " + messageOf(e));
        }
        pickDestKind = "auto";
    }

    private int countFiles(File dir) {
        if (dir == null || !dir.isDirectory()) {
            return 0;
        }
        File[] files = dir.listFiles();
        if (files == null) {
            return 0;
        }
        int n = 0;
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null || !file.isFile()) {
                continue;
            }
            String fname = file.getName();
            if (fname == null || fname.startsWith(".") || "README.txt".equalsIgnoreCase(fname)
                    || ".nomedia".equals(fname)) {
                continue;
            }
            n++;
        }
        return n;
    }

    private void diskSnapshotNow() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        File chars = new File(sideloadDir, "characters");
        File bgm = new File(sideloadDir, "custom_bgm");
        File chess = new File(sideloadDir, "chess_games");
        File piano = new File(sideloadDir, "piano_songs");
        File saves = savesDir();
        File wallpaper = new File(sideloadDir, "custom_wallpaper.png");
        File monika = new File(chars, "monika");
        String packs = SubmodInstaller.listReport(sideloadDir);
        StringBuilder out = new StringBuilder();
        out.append("\n=== снимок Documents ===");
        out.append("\nпуть: ").append(sideloadDir.getAbsolutePath());
        out.append("\nдоступ ко всем файлам: ").append(canUseDocuments());
        out.append("\ncharacters: ").append(countFiles(chars)).append("  (monika=")
                .append(monika.isFile() ? (monika.length() + " байт") : "нет").append(")");
        out.append("\ncustom_bgm: ").append(countFiles(bgm));
        out.append("\nchess_games: ").append(countFiles(chess));
        out.append("\npiano_songs: ").append(countFiles(piano));
        out.append("\nsaves: ").append(countFiles(saves));
        out.append("\n_mas/archives: ").append(countFiles(archivesDir));
        out.append("\nобои: ").append(wallpaper.isFile()
                ? (wallpaper.length() + " байт") : "нет");
        out.append("\n").append(packs);
        appendStatus(out.toString());
        logLine("disk snapshot chars=" + countFiles(chars)
                + " bgm=" + countFiles(bgm)
                + " chess=" + countFiles(chess)
                + " piano=" + countFiles(piano)
                + " saves=" + countFiles(saves));
        evalJs("biosSubmods", SubmodInstaller.listJson(sideloadDir));
        pushStatusToPage();
    }

    private void openDocumentsNow() {
        if (sideloadDir == null) {
            resolvePaths();
        }
        logLine("open documents " + sideloadDir.getAbsolutePath());
        try {
            Uri uri = Uri.parse(
                    "content://com.android.externalstorage.documents/document/primary%3ADocuments%2FMonika_after_story"
            );
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "vnd.android.document/directory");
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            appendStatus("\nОткрываю Documents/Monika_after_story");
            return;
        } catch (Exception e) {
            logLine("open documents view failed " + messageOf(e));
        }
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(Uri.fromFile(sideloadDir), "*/*");
            startActivity(Intent.createChooser(intent, "Documents"));
            appendStatus("\nОткрываю " + sideloadDir.getAbsolutePath());
        } catch (Exception e) {
            appendStatus("\nПапка: " + sideloadDir.getAbsolutePath()
                    + "\nОткрой её в любом файловом менеджере.");
            logLine("open documents chooser failed " + messageOf(e));
        }
    }

    private void copyWallpaper(Uri uri) {
        File dest = new File(sideloadDir, "custom_wallpaper.png");
        try {
            if (dest.getParentFile() != null && !dest.getParentFile().isDirectory()) {
                dest.getParentFile().mkdirs();
            }
            long bytes = copyUriToFile(uri, dest);
            String name = displayName(uri);
            appendStatus("\nКартинка " + name + ", байт " + bytes + "\n" + dest.getAbsolutePath());
            logLine("wallpaper " + name + " bytes " + bytes + " " + dest.getAbsolutePath());
        } catch (Exception e) {
            appendStatus("\nКартинка не скопирована: " + messageOf(e));
            logLine("wallpaper failed " + messageOf(e));
        }
    }

    private void copyPickedZip(Uri uri) {
        String name = displayName(uri);
        if (name != null && !name.toLowerCase(Locale.US).endsWith(".zip")) {
            appendStatus("\nЭто не zip: " + name);
            logLine("pick not zip " + name);
            return;
        }
        if (incomingDir == null) {
            resolvePaths();
        }
        if (!incomingDir.isDirectory() && !incomingDir.mkdirs()) {
            appendStatus("\nПапка архивов не создана.");
            logLine("pick zip no archives");
            return;
        }
        File dest = new File(incomingDir, "picked.zip");
        try {
            long bytes = copyUriToFile(uri, dest);
            appendStatus("\nZip " + name + ", байт " + bytes + "\n" + dest.getAbsolutePath());
            logLine("picked zip " + name + " bytes " + bytes);
            installSubmodFile(dest);
        } catch (Exception e) {
            appendStatus("\nZip не скопирован: " + messageOf(e));
            logLine("picked zip failed " + messageOf(e));
        }
    }

    private boolean zipHasExtraHello(File zip) {
        ZipFile zipFile = null;
        try {
            zipFile = new ZipFile(zip);
            Enumeration<? extends ZipEntry> entries = zipFile.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (entry.isDirectory()) {
                    continue;
                }
                String name = entry.getName();
                if (name == null) {
                    continue;
                }
                String norm = name.replace('\\', '/');
                if (norm.endsWith("extra_hello.rpy")) {
                    return true;
                }
            }
        } catch (Exception e) {
            appendStatus("\nАрхив не прочитан: " + messageOf(e));
            logLine("picked zip read failed " + messageOf(e));
        } finally {
            if (zipFile != null) {
                try {
                    zipFile.close();
                } catch (IOException ignored) {
                }
            }
        }
        return false;
    }

    private long copyUriToFile(Uri uri, File dest) throws IOException {
        InputStream in = null;
        FileOutputStream out = null;
        try {
            in = getContentResolver().openInputStream(uri);
            if (in == null) {
                throw new IOException("пустой поток");
            }
            out = new FileOutputStream(dest);
            byte[] buf = new byte[8192];
            long total = 0;
            int n;
            while ((n = in.read(buf)) >= 0) {
                if (n > 0) {
                    out.write(buf, 0, n);
                    total += n;
                }
            }
            out.flush();
            return total;
        } finally {
            if (in != null) {
                try {
                    in.close();
                } catch (IOException ignored) {
                }
            }
            if (out != null) {
                try {
                    out.close();
                } catch (IOException ignored) {
                }
            }
        }
    }

    private String displayName(Uri uri) {
        Cursor cursor = null;
        try {
            cursor = getContentResolver().query(uri, new String[] {OpenableColumns.DISPLAY_NAME}, null, null, null);
            if (cursor != null && cursor.moveToFirst()) {
                int index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);
                if (index >= 0) {
                    return cursor.getString(index);
                }
            }
        } catch (Exception ignored) {
        } finally {
            if (cursor != null) {
                cursor.close();
            }
        }
        return uri.getLastPathSegment();
    }

    private void checkUpdate() {
        appendStatus("\nПроверяю релиз.");
        new Thread(new Runnable() {
            @Override
            public void run() {
                checkUpdateInBackground();
            }
        }).start();
    }

    private void checkUpdateInBackground() {
        HttpURLConnection conn = null;
        try {
            conn = openGet(RELEASES_URL);
            int code = conn.getResponseCode();
            if (code == 404) {
                updateApkUrl = null;
                postStatus("\nРелиза нет.");
                logLine("release missing");
                return;
            }
            if (code != HttpURLConnection.HTTP_OK) {
                postStatus("\nСервер релизов ответил " + code);
                logLine("release http " + code);
                return;
            }
            String body = readStream(conn.getInputStream());
            JSONObject root = new JSONObject(body);
            String tag = root.optString("tag_name", "");
            JSONArray assets = root.optJSONArray("assets");
            StringBuilder report = new StringBuilder();
            report.append("\nРелиз ").append(tag.length() == 0 ? "(без tag)" : tag);
            String apkUrl = null;
            String apkName = null;
            String digest = null;
            String shaUrl = null;
            long apkSize = -1L;
            if (assets != null) {
                for (int i = 0; i < assets.length(); i++) {
                    JSONObject asset = assets.optJSONObject(i);
                    if (asset == null) {
                        continue;
                    }
                    String name = asset.optString("name", "");
                    report.append("\nasset ").append(name);
                    String lower = name.toLowerCase(Locale.US);
                    if (apkUrl == null && lower.endsWith(".apk")) {
                        apkUrl = asset.optString("browser_download_url", "");
                        apkName = name;
                        digest = asset.optString("digest", "");
                        apkSize = asset.optLong("size", -1L);
                    }
                }
                if (apkName != null) {
                    String shaName = apkName + ".sha256";
                    for (int i = 0; i < assets.length(); i++) {
                        JSONObject asset = assets.optJSONObject(i);
                        if (asset != null && shaName.equals(asset.optString("name", ""))) {
                            shaUrl = asset.optString("browser_download_url", "");
                        }
                    }
                }
            }
            updateApkUrl = apkUrl;
            updateApkName = apkName;
            updateApkDigest = digest;
            updateApkShaUrl = shaUrl;
            updateAssetSize = apkSize;
            long installed = currentVersionCode();
            String installedName = currentVersionName();
            report.append("\nсвоя версия ").append(installedName);
            report.append(" versionCode ").append(installed);
            report.append("\nрелиз ").append(tag);
            boolean localReady = localApkMatches(apkSize, digest);
            int compare = compareRelease(tag, installedName, installed);
            if (apkUrl == null || apkUrl.length() == 0) {
                updateApkUrl = null;
                updateNeeded = false;
                report.append("\nВ релизе нет apk.");
                report.append("\nкачалка не нужна");
            } else if (compare < 0) {
                updateNeeded = false;
                report.append("\nуже последняя");
                report.append("\nкачалка не нужна");
            } else if (compare == 0) {
                updateNeeded = true;
                report.append("\nверсию сравнить не удалось");
                report.append("\nкачалка нужна");
            } else {
                updateNeeded = true;
                report.append("\nкачалка нужна");
            }
            if (localReady) {
                report.append("\nскачанный apk совпал, повторно качать не нужно");
            }
            if (apkName != null) {
                report.append("\nНайден ").append(apkName);
            }
            postStatus(report.toString());
            logLine("release " + tag + " apk " + apkName);
        } catch (Exception e) {
            postStatus("\nПроверка релиза не удалась: " + messageOf(e));
            logLine("release failed " + messageOf(e));
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }

    private void downloadUpdate() {
        if (downloadRunning) {
            if (downloadPaused) {
                appendStatus("\nСкачивание на паузе. Нажми Продолжить или Отмена.");
            } else {
                appendStatus("\nСкачивание уже идёт. Можно поставить на паузу.");
            }
            return;
        }
        downloadCancel = false;
        downloadPaused = false;
        downloadRunning = true;
        appendStatus("\nГотовлю apk.");
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    if (updateApkUrl == null || updateApkUrl.length() == 0) {
                        checkUpdateInBackground();
                    }
                    if (updateApkUrl == null || updateApkUrl.length() == 0) {
                        postStatus("\nКачать нечего: apk в релизе нет.");
                        return;
                    }
                    File existing = new File(getFilesDir(), "update.apk");
                    if (localApkMatches(updateAssetSize, updateApkDigest)) {
                        final File ready = existing;
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                appendStatus("\nAPK уже скачан, открываю установщик.");
                                installDownloadedApk(ready);
                            }
                        });
                        return;
                    }
                    if (!updateNeeded) {
                        postStatus("\nуже последняя");
                        logLine("apk up to date");
                        return;
                    }
                    String expected = updateApkDigest;
                    if (normalizeHash(expected) == null && updateApkShaUrl != null && updateApkShaUrl.length() > 0) {
                        expected = fetchOptionalSha(updateApkShaUrl);
                    }
                    final File dest = new File(getFilesDir(), "update.apk");
                    boolean ok = downloadUrlToFile(updateApkUrl, dest, expected);
                    if (!ok) {
                        return;
                    }
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            installDownloadedApk(dest);
                        }
                    });
                } finally {
                    downloadRunning = false;
                }
            }
        }).start();
    }

    private void installLocalApk() {
        File dest = new File(getFilesDir(), "update.apk");
        if (!dest.isFile()) {
            appendStatus("\nСкачанного apk нет.");
            logLine("local apk missing");
            return;
        }
        appendStatus("\nСтавлю скачанный apk без повторной загрузки.");
        installDownloadedApk(dest);
    }

    private void downloadUpdateAgain() {
        if (downloadRunning) {
            if (downloadPaused) {
                appendStatus("\nСкачивание на паузе. Нажми Продолжить или Отмена.");
            } else {
                appendStatus("\nСкачивание уже идёт. Можно поставить на паузу.");
            }
            return;
        }
        downloadCancel = false;
        downloadPaused = false;
        downloadRunning = true;
        appendStatus("\nКачаю apk заново.");
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    if (updateApkUrl == null || updateApkUrl.length() == 0) {
                        checkUpdateInBackground();
                    }
                    if (updateApkUrl == null || updateApkUrl.length() == 0) {
                        postStatus("\nКачать нечего: apk в релизе нет.");
                        return;
                    }
                    String expected = updateApkDigest;
                    if (normalizeHash(expected) == null && updateApkShaUrl != null && updateApkShaUrl.length() > 0) {
                        expected = fetchOptionalSha(updateApkShaUrl);
                    }
                    final File dest = new File(getFilesDir(), "update.apk");
                    boolean ok = downloadUrlToFile(updateApkUrl, dest, expected);
                    if (!ok) {
                        return;
                    }
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            installDownloadedApk(dest);
                        }
                    });
                } finally {
                    downloadRunning = false;
                }
            }
        }).start();
    }

    private boolean localApkMatches(long size, String digest) {
        File apk = new File(getFilesDir(), "update.apk");
        if (!apk.isFile()) {
            return false;
        }
        String hash = normalizeHash(digest);
        if (hash != null) {
            try {
                return hash.equals(sha256(apk));
            } catch (Exception e) {
                return false;
            }
        }
        return size > 0 && apk.length() == size;
    }

    private int compareRelease(String tag, String versionName, long versionCode) {
        String plain = tag == null ? "" : tag.trim();
        if (plain.startsWith("v") || plain.startsWith("V")) {
            plain = plain.substring(1);
        }
        if (versionName != null && plain.length() > 0 && plain.equals(versionName)) {
            return -1;
        }
        try {
            if (plain.length() > 0) {
                long tagCode = Long.parseLong(plain);
                if (versionCode >= 0 && tagCode <= versionCode) {
                    return -1;
                }
                if (versionCode >= 0 && tagCode > versionCode) {
                    return 1;
                }
            }
        } catch (NumberFormatException ignored) {
        }
        return 0;
    }

    private String currentVersionName() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return info.versionName == null ? "" : info.versionName;
        } catch (Exception e) {
            return "";
        }
    }

    private void installDownloadedApk(File apk) {
        if (Build.VERSION.SDK_INT >= 26 && !getPackageManager().canRequestPackageInstalls()) {
            appendStatus("\nРазреши установку из этого приложения, потом нажми кнопку снова.");
            logLine("need REQUEST_INSTALL_PACKAGES");
            try {
                Intent settings = new Intent(Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES);
                settings.setData(Uri.parse("package:" + getPackageName()));
                startActivity(settings);
            } catch (Exception e) {
                appendStatus("\nНастройки установки не открылись: " + messageOf(e));
            }
            return;
        }
        try {
            Uri uri = FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", apk);
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "application/vnd.android.package-archive");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
            startActivity(intent);
            appendStatus("\nОткрыл установщик " + apk.getName());
            logLine("install apk " + apk.getAbsolutePath());
        } catch (Exception e) {
            appendStatus("\nУстановщик не открылся: " + messageOf(e));
            logLine("install apk failed " + messageOf(e));
        }
    }

    private long currentVersionCode() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            if (Build.VERSION.SDK_INT >= 28) {
                return info.getLongVersionCode();
            }
            return info.versionCode;
        } catch (Exception e) {
            return -1L;
        }
    }

    private String readStream(InputStream in) throws IOException {
        byte[] buf = new byte[4096];
        StringBuilder body = new StringBuilder();
        int n;
        while ((n = in.read(buf)) >= 0) {
            if (n > 0) {
                body.append(new String(buf, 0, n, "UTF-8"));
            }
        }
        in.close();
        return body.toString();
    }

    private void shareSaves() {
        if (newestBackupZip() == null) {
            exportSaves();
        }
        File zip = newestBackupZip();
        if (zip == null || !zip.isFile()) {
            appendStatus("\nПоделиться: нет zip бэкапа.");
            logLine("share no zip");
            return;
        }
        try {
            String authority = getPackageName() + ".fileprovider";
            Uri uri = FileProvider.getUriForFile(this, authority, zip);
            Intent send = new Intent(Intent.ACTION_SEND);
            send.setType("application/zip");
            send.putExtra(Intent.EXTRA_STREAM, uri);
            send.setClipData(ClipData.newRawUri("saves", uri));
            send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            Intent chooser = Intent.createChooser(send, "Отправить бэкап");
            chooser.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(chooser);
            appendStatus("\nПоделиться " + zip.getAbsolutePath());
            logLine("share " + zip.getAbsolutePath());
        } catch (Exception e) {
            appendStatus("\nПоделиться не удалось: " + messageOf(e));
            logLine("share failed " + messageOf(e));
        }
    }

    private void importSaves() {
        File zip = newestBackupZip();
        String from = "backups";
        if (zip == null && incomingDir != null) {
            File incomingZip = new File(incomingDir, "saves.zip");
            if (incomingZip.isFile()) {
                zip = incomingZip;
                from = "archives";
            }
        }
        if (zip == null) {
            appendStatus("\nИмпорт: нет zip в _mas/backups и нет _mas/archives/saves.zip.");
            logLine("import no zip");
            return;
        }
        File saves = savesDir();
        if (!saves.isDirectory() && !saves.mkdirs()) {
            appendStatus("\nИмпорт: не создана папка saves.");
            logLine("import saves mkdir failed");
            return;
        }
        int count = unzipReplace(zip, saves);
        appendStatus("\nИмпорт " + from + " " + zip.getAbsolutePath() + ", файлов: " + count);
        logLine("import " + zip.getAbsolutePath() + " files " + count);
    }

    private File newestBackupZip() {
        File backups = backupsDir();
        File[] files = backups.listFiles();
        if (files == null) {
            return null;
        }
        File best = null;
        long bestTime = -1L;
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null || !file.isFile()) {
                continue;
            }
            String name = file.getName();
            if (name == null || !name.toLowerCase(Locale.US).endsWith(".zip")) {
                continue;
            }
            long when = file.lastModified();
            if (best == null || when > bestTime) {
                best = file;
                bestTime = when;
            }
        }
        return best;
    }

    private int unzipReplace(File zip, File destDir) {
        ZipFile zipFile = null;
        int count = 0;
        try {
            zipFile = new ZipFile(zip);
            Enumeration<? extends ZipEntry> entries = zipFile.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                String name = entry.getName();
                if (forbiddenZipName(name)) {
                    appendStatus("\nПропущен путь с .. : " + name);
                    logLine("import reject " + name);
                    continue;
                }
                String relative = name.replace('\\', '/');
                File out = new File(destDir, relative);
                if (!staysInside(destDir, out)) {
                    appendStatus("\nПропущен путь вне saves: " + name);
                    logLine("import outside " + name);
                    continue;
                }
                if (entry.isDirectory() || relative.endsWith("/")) {
                    if (!out.isDirectory() && !out.mkdirs()) {
                        appendStatus("\nНе создан каталог " + relative);
                    }
                    continue;
                }
                File parent = out.getParentFile();
                if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
                    appendStatus("\nНе создан каталог для " + relative);
                    continue;
                }
                copyEntry(zipFile, entry, out);
                count++;
            }
        } catch (Exception e) {
            appendStatus("\nИмпорт не удался: " + messageOf(e));
            logLine("import failed " + messageOf(e));
        } finally {
            if (zipFile != null) {
                try {
                    zipFile.close();
                } catch (IOException ignored) {
                }
            }
        }
        return count;
    }



    private org.json.JSONArray archivePacks() {
        if (archivePacks != null) {
            return archivePacks;
        }
        archivePacks = new org.json.JSONArray();
        String raw = readArchivesJson();
        if (raw != null) {
            try {
                org.json.JSONObject root = new org.json.JSONObject(raw);
                org.json.JSONArray packs = root.optJSONArray("packs");
                if (packs != null) {
                    archivePacks = packs;
                    return archivePacks;
                }
            } catch (Exception e) {
                logLine("archives.json: " + messageOf(e));
            }
        }
        try {
            archivePacks.put(defaultPack("images", "images.rpa", "Картинки DDLC", "images/bg/bedroom.png"));
            archivePacks.put(defaultPack("audio", "audio.rpa", "Музыка и звуки", "bgm/1.ogg"));
        } catch (Exception ignored) {
        }
        return archivePacks;
    }

    private org.json.JSONObject defaultPack(String id, String file, String title, String marker) throws Exception {
        org.json.JSONObject pack = new org.json.JSONObject();
        pack.put("id", id);
        pack.put("file", file);
        pack.put("title", title);
        pack.put("marker", marker);
        pack.put("required", true);
        pack.put("sha256", "");
        pack.put("bytes", 0);
        return pack;
    }

    private String archivesBaseUrl() {
        String raw = readArchivesJson();
        if (raw == null) {
            return "https://github.com/artem213101zse/MonikaModDev-RU/releases/latest/download/";
        }
        try {
            String url = new org.json.JSONObject(raw).optString("base_url", "");
            if (url.length() > 0) {
                if (!url.endsWith("/")) {
                    url = url + "/";
                }
                return url;
            }
        } catch (Exception ignored) {
        }
        return "https://github.com/artem213101zse/MonikaModDev-RU/releases/latest/download/";
    }

    private String readArchivesJson() {
        File www = new File(new File(getFilesDir(), "bios_www"), "archives.json");
        if (www.isFile()) {
            String text = readTextFile(www);
            if (text != null) {
                return text;
            }
        }
        try {
            InputStream in = getAssets().open("www/archives.json");
            return readStreamText(in);
        } catch (Exception ignored) {
        }
        try {
            InputStream in = getResources().openRawResource(R.raw.bios_archives);
            return readStreamText(in);
        } catch (Exception ignored) {
        }
        return null;
    }

    private String readTextFile(File file) {
        FileInputStream in = null;
        try {
            in = new FileInputStream(file);
            return readStreamText(in);
        } catch (Exception e) {
            return null;
        } finally {
            closeQuietly(in);
        }
    }

    private String readStreamText(InputStream in) throws IOException {
        byte[] buf = new byte[8192];
        java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
        int n;
        while ((n = in.read(buf)) >= 0) {
            if (n > 0) {
                out.write(buf, 0, n);
            }
        }
        in.close();
        return out.toString("UTF-8");
    }

    private boolean packReady(org.json.JSONObject pack) {
        if (pack == null) {
            return false;
        }
        String marker = pack.optString("marker", "");
        if (marker.length() > 0 && gameOverlayDir != null) {
            if (new File(gameOverlayDir, marker).isFile()) {
                return true;
            }
        }
        String file = pack.optString("file", "");
        if (file.length() > 0 && gameOverlayDir != null) {
            if (new File(gameOverlayDir, file).isFile()) {
                return true;
            }
        }
        return apkHasPack(pack);
    }

    private boolean apkHasPack(org.json.JSONObject pack) {
        String marker = pack.optString("marker", "");
        if (marker.length() == 0) {
            return false;
        }
        StringBuilder asset = new StringBuilder("x-game");
        String[] bits = marker.replace('\\', '/').split("/");
        for (int i = 0; i < bits.length; i++) {
            if (bits[i].length() == 0) {
                continue;
            }
            asset.append("/x-").append(bits[i]);
        }
        try {
            InputStream in = getAssets().open(asset.toString());
            in.close();
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private boolean archivesReady() {
        org.json.JSONArray packs = archivePacks();
        for (int i = 0; i < packs.length(); i++) {
            org.json.JSONObject pack = packs.optJSONObject(i);
            if (pack == null) {
                continue;
            }
            if (pack.optBoolean("required", true) && !packReady(pack)) {
                return false;
            }
        }
        return true;
    }

    private void reportArchiveStatus() {
        org.json.JSONArray packs = archivePacks();
        StringBuilder report = new StringBuilder();
        report.append("\nАрхивы:");
        int missing = 0;
        for (int i = 0; i < packs.length(); i++) {
            org.json.JSONObject pack = packs.optJSONObject(i);
            if (pack == null) {
                continue;
            }
            boolean ok = packReady(pack);
            if (!ok) {
                missing++;
            }
            report.append("\n").append(ok ? "есть " : "нет  ");
            report.append(pack.optString("title", pack.optString("file", "?")));
        }
        if (missing == 0) {
            report.append("\nвсё на месте, можно запускать MAS");
        } else {
            report.append("\nне хватает ").append(missing);
            report.append(". Скачай с ddlc.moe / GitHub или положи .rpa / ddlc-win.zip в _mas/archives");
        }
        appendStatus(report.toString());
    }

    private void downloadArchives() {
        if (downloadRunning) {
            if (downloadPaused) {
                appendStatus("\nСкачивание на паузе. Нажми Продолжить или Отмена.");
            } else {
                appendStatus("\nСкачивание уже идёт. Можно поставить на паузу.");
            }
            return;
        }
        if (sideloadDir == null) {
            resolvePaths();
        }
        if (!canUseDocuments()) {
            appendStatus("\nНет доступа ко всем файлам. MAS пишет в Documents/Monika_after_story.");
            if (needsRuntimePermission()) {
                requestPermissions(new String[] {
                        android.Manifest.permission.READ_EXTERNAL_STORAGE,
                        android.Manifest.permission.WRITE_EXTERNAL_STORAGE
                }, REQ_STORAGE);
            } else {
                openAllFilesSettings();
            }
            pushStatusToPage();
            return;
        }
        if (archivesDir == null || (!archivesDir.isDirectory() && !archivesDir.mkdirs())) {
            appendStatus("\nНет папки archives.");
            return;
        }
        downloadCancel = false;
        downloadPaused = false;
        downloadRunning = true;
        appendStatus("\nКачаю архивы DDLC.");
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    org.json.JSONArray packs = archivePacks();
                    String base = archivesBaseUrl();
                    int got = 0;
                    for (int i = 0; i < packs.length(); i++) {
                        org.json.JSONObject pack = packs.optJSONObject(i);
                        if (pack == null) {
                            continue;
                        }
                        if (packReady(pack)) {
                            postStatus("\nуже есть " + pack.optString("title", pack.optString("file")));
                            got++;
                            continue;
                        }
                        String file = pack.optString("file", "");
                        if (file.length() == 0) {
                            continue;
                        }
                        String url = pack.optString("url", "");
                        if (url.length() == 0) {
                            url = base + file;
                        }
                        String expected = normalizeHash(pack.optString("sha256", ""));
                        if (expected == null) {
                            expected = fetchOptionalSha(url + ".sha256");
                        }
                        File dest = new File(archivesDir, file);
                        postStatus("\nкачаю " + file);
                        boolean ok = downloadUrlToFile(url, dest, expected);
                        if (!ok) {
                            if (downloadCancel) {
                                postStatus("\nархивы: отменено");
                                break;
                            }
                            continue;
                        }
                        if (unpackRpaFile(dest)) {
                            got++;
                        }
                    }
                    cleanupAfterUnpack();
                    postStatus("\nархивов готово: " + got);
                    reportArchiveStatus();
                } finally {
                    downloadRunning = false;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            pushStatusToPage();
                        }
                    });
                }
            }
        }).start();
    }

    private void downloadDdlcMoe() {
        if (downloadRunning) {
            if (downloadPaused) {
                appendStatus("\nСкачивание на паузе. Нажми Продолжить или Отмена.");
            } else {
                appendStatus("\nСкачивание уже идёт. Можно поставить на паузу.");
            }
            return;
        }
        if (sideloadDir == null) {
            resolvePaths();
        }
        if (!canUseDocuments()) {
            appendStatus("\nНет доступа ко всем файлам. MAS пишет в Documents/Monika_after_story.");
            if (needsRuntimePermission()) {
                requestPermissions(new String[] {
                        android.Manifest.permission.READ_EXTERNAL_STORAGE,
                        android.Manifest.permission.WRITE_EXTERNAL_STORAGE
                }, REQ_STORAGE);
            } else {
                openAllFilesSettings();
            }
            pushStatusToPage();
            return;
        }
        if (archivesDir == null || (!archivesDir.isDirectory() && !archivesDir.mkdirs())) {
            appendStatus("\nНет папки archives.");
            return;
        }
        downloadCancel = false;
        downloadPaused = false;
        downloadRunning = true;
        appendStatus("\nКачаю DDLC с ddlc.moe.");
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    File zip = new File(archivesDir, ddlcZipName());
                    if (zipLooksLikeDdlc(zip)) {
                        postStatus("\nzip уже на диске: " + zip.getName());
                    } else {
                        String url = resolveDdlcZipUrl();
                        if (url == null || url.length() == 0) {
                            postStatus("\nНе удалось получить ссылку с ddlc.moe.");
                            return;
                        }
                        postStatus("\nкачаю " + zip.getName());
                        if (!downloadUrlToFile(url, zip, null, true)) {
                            postStatus("\nZip с ddlc.moe не скачался.");
                            return;
                        }
                    }
                    installDdlcZip(zip);
                    reportArchiveStatus();
                } catch (Exception e) {
                    postStatus("\nDDLC с ddlc.moe: " + messageOf(e));
                    logLine("ddlc.moe failed " + messageOf(e));
                } finally {
                    downloadRunning = false;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            pushStatusToPage();
                        }
                    });
                }
            }
        }).start();
    }

    private String resolveDdlcZipUrl() throws Exception {
        DdlcItch.ensureCookies();
        org.json.JSONArray directs = ddlcDirectUrls();
        for (int i = 0; i < directs.length(); i++) {
            String url = directs.optString(i, "");
            if (url.length() == 0) {
                continue;
            }
            postStatus("\nпроверяю " + url);
            if (DdlcItch.urlLooksLikeZip(url)) {
                return url;
            }
        }
        org.json.JSONObject cfg = ddlcConfig();
        String itch = cfg.optString("itch_game", DdlcItch.DEFAULT_ITCH);
        String name = cfg.optString("upload_name", DdlcItch.DEFAULT_UPLOAD);
        postStatus("\nddlc.moe → itch.io, файл " + name);
        return DdlcItch.resolveZipUrl(itch, name);
    }

    private boolean installDdlcZip(File zip) {
        preferApkFonts();
        if (zip == null || !zip.isFile()) {
            postStatus("\nНет zip DDLC.");
            return false;
        }
        if (!zipLooksLikeDdlc(zip)) {
            postStatus("\n" + zip.getName() + " не похож на ddlc-win.zip");
            return false;
        }
        File stash = new File(archivesDir, "ddlc");
        if (!stash.isDirectory() && !stash.mkdirs()) {
            postStatus("\nНет папки archives/ddlc.");
            return false;
        }
        postStatus("\nдостаю .rpa из " + zip.getName());
        int extracted = extractOfficialRpas(zip, stash);
        if (extracted <= 0) {
            postStatus("\nВ zip нет images.rpa / audio.rpa.");
            return false;
        }
        int ready = 0;
        String[] names = officialRpaNames();
        for (int i = 0; i < names.length; i++) {
            File rpa = new File(stash, names[i]);
            if (!rpa.isFile()) {
                continue;
            }
            if (gameOverlayDir != null) {
                if (!gameOverlayDir.isDirectory() && !gameOverlayDir.mkdirs()) {
                    postStatus("\nНет папки game для " + names[i]);
                    continue;
                }
                if (shouldCopyOfficialRpa(names[i])) {
                    copyFile(rpa, new File(gameOverlayDir, names[i]));
                } else {
                    postStatus("\n" + names[i] + " не кладу в overlay — берутся файлы из APK");
                    File shadowed = new File(gameOverlayDir, names[i]);
                    if (shadowed.isFile()) {
                        shadowed.delete();
                    }
                }
            }
            if (shouldUnpackOfficialRpa(names[i])) {
                if (unpackRpaFile(rpa, false)) {
                    ready++;
                }
            } else {
                postStatus("\n" + names[i] + " оставлен архивом");
                ready++;
            }
        }
        postStatus("\nиз ddlc.moe готово паков: " + ready);
        if (ready > 0) {
            cleanupAfterUnpack();
        }
        return ready > 0;
    }

    private int extractOfficialRpas(File zip, File destDir) {
        ZipFile zipFile = null;
        int count = 0;
        try {
            zipFile = new ZipFile(zip);
            Enumeration<? extends ZipEntry> entries = zipFile.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (entry == null || entry.isDirectory()) {
                    continue;
                }
                String name = entry.getName();
                if (forbiddenZipName(name)) {
                    continue;
                }
                String base = rpaBaseName(name);
                if (base == null || !isOfficialRpaName(base)) {
                    continue;
                }
                File out = new File(destDir, base);
                if (!staysInside(destDir, out)) {
                    continue;
                }
                postStatus("\nиз zip: " + base);
                copyEntry(zipFile, entry, out);
                count++;
            }
        } catch (Exception e) {
            postStatus("\nНе разобрать zip: " + messageOf(e));
            logLine("ddlc zip extract failed " + messageOf(e));
        } finally {
            if (zipFile != null) {
                try {
                    zipFile.close();
                } catch (IOException ignored) {
                }
            }
        }
        return count;
    }

    private boolean zipLooksLikeDdlc(File zip) {
        if (zip == null || !zip.isFile()) {
            return false;
        }
        ZipFile zipFile = null;
        try {
            zipFile = new ZipFile(zip);
            Enumeration<? extends ZipEntry> entries = zipFile.entries();
            while (entries.hasMoreElements()) {
                ZipEntry entry = entries.nextElement();
                if (entry == null) {
                    continue;
                }
                String base = rpaBaseName(entry.getName());
                if (base != null && isOfficialRpaName(base)) {
                    return true;
                }
            }
        } catch (Exception e) {
            return false;
        } finally {
            if (zipFile != null) {
                try {
                    zipFile.close();
                } catch (IOException ignored) {
                }
            }
        }
        return false;
    }

    private String rpaBaseName(String path) {
        if (path == null) {
            return null;
        }
        String relative = path.replace('\\', '/');
        int slash = relative.lastIndexOf('/');
        String base = slash >= 0 ? relative.substring(slash + 1) : relative;
        if (base.length() == 0) {
            return null;
        }
        if (!base.toLowerCase(Locale.US).endsWith(".rpa")) {
            return null;
        }
        return base;
    }

    private org.json.JSONObject ddlcConfig() {
        String raw = readArchivesJson();
        if (raw != null) {
            try {
                org.json.JSONObject root = new org.json.JSONObject(raw);
                org.json.JSONObject ddlc = root.optJSONObject("ddlc");
                if (ddlc != null) {
                    return ddlc;
                }
            } catch (Exception ignored) {
            }
        }
        return new org.json.JSONObject();
    }

    private String ddlcZipName() {
        String name = ddlcConfig().optString("file", "ddlc-win.zip");
        if (name.length() == 0) {
            return "ddlc-win.zip";
        }
        return name;
    }

    private org.json.JSONArray ddlcDirectUrls() {
        org.json.JSONArray urls = ddlcConfig().optJSONArray("direct_urls");
        if (urls != null) {
            return urls;
        }
        return new org.json.JSONArray();
    }

    private String[] officialRpaNames() {
        org.json.JSONArray arr = ddlcConfig().optJSONArray("rpas");
        if (arr == null || arr.length() == 0) {
            return new String[] { "images.rpa", "audio.rpa", "fonts.rpa", "scripts.rpa" };
        }
        String[] names = new String[arr.length()];
        for (int i = 0; i < arr.length(); i++) {
            names[i] = arr.optString(i, "");
        }
        return names;
    }

    private boolean isOfficialRpaName(String name) {
        if (name == null) {
            return false;
        }
        String[] names = officialRpaNames();
        String lower = name.toLowerCase(Locale.US);
        for (int i = 0; i < names.length; i++) {
            if (lower.equals(names[i].toLowerCase(Locale.US))) {
                return true;
            }
        }
        return false;
    }

    private boolean shouldUnpackOfficialRpa(String name) {
        if (name == null) {
            return false;
        }
        String lower = name.toLowerCase(Locale.US);
        if (lower.equals("scripts.rpa")) {
            return false;
        }
        if (lower.equals("fonts.rpa") && apkHasRelative("gui/font/Aller_Rg.ttf")) {
            return false;
        }
        org.json.JSONArray arr = ddlcConfig().optJSONArray("unpack");
        if (arr == null || arr.length() == 0) {
            return !lower.equals("scripts.rpa") && !lower.equals("fonts.rpa");
        }
        for (int i = 0; i < arr.length(); i++) {
            if (lower.equals(arr.optString(i, "").toLowerCase(Locale.US))) {
                return true;
            }
        }
        return false;
    }

    private boolean shouldCopyOfficialRpa(String name) {
        if (name == null) {
            return false;
        }
        String lower = name.toLowerCase(Locale.US);
        if (lower.equals("fonts.rpa") && apkHasRelative("gui/font/Aller_Rg.ttf")) {
            return false;
        }
        return true;
    }

    private boolean apkHasRelative(String relative) {
        if (relative == null || relative.length() == 0) {
            return false;
        }
        StringBuilder asset = new StringBuilder("x-game");
        String[] bits = relative.replace('\\', '/').split("/");
        for (int i = 0; i < bits.length; i++) {
            if (bits[i].length() == 0) {
                continue;
            }
            asset.append("/x-").append(bits[i]);
        }
        try {
            InputStream in = getAssets().open(asset.toString());
            in.close();
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    private void preferApkFonts() {
        if (gameOverlayDir == null) {
            return;
        }
        if (apkHasRelative("gui/font/Aller_Rg.ttf")) {
            File overlayRpa = new File(gameOverlayDir, "fonts.rpa");
            if (overlayRpa.isFile() && overlayRpa.delete()) {
                postStatus("\nfonts.rpa убран из overlay — остаются шрифты с кириллицей");
            }
        }
        File fontDir = new File(new File(gameOverlayDir, "gui"), "font");
        if (!fontDir.isDirectory()) {
            return;
        }
        File[] files = fontDir.listFiles();
        if (files == null) {
            return;
        }
        int dropped = 0;
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null || !file.isFile()) {
                continue;
            }
            String rel = "gui/font/" + file.getName();
            if (apkHasRelative(rel) && file.delete()) {
                dropped++;
            }
        }
        if (dropped > 0) {
            postStatus("\nиз overlay убраны шрифты, которые уже есть в APK: " + dropped);
        }
    }

    private boolean isZipFile(File file) {
        if (file == null || !file.isFile()) {
            return false;
        }
        FileInputStream in = null;
        try {
            in = new FileInputStream(file);
            byte[] magic = new byte[4];
            int n = in.read(magic);
            return n >= 4 && magic[0] == 'P' && magic[1] == 'K';
        } catch (Exception e) {
            return false;
        } finally {
            closeQuietly(in);
        }
    }

    private void installDroppedArchives(boolean quiet) {
        if (downloadRunning) {
            if (!quiet) {
                postStatus("\nУже идёт работа с архивами.");
            }
            return;
        }
        downloadRunning = true;
        try {
            if (sideloadDir == null) {
                resolvePaths();
            }
            List<File> found = new ArrayList<File>();
            addRpaFiles(found, archivesDir);
            addRpaFiles(found, sideloadDir);
            addDdlcZips(found, archivesDir);
            addDdlcZips(found, sideloadDir);
            if (found.isEmpty()) {
                if (!quiet) {
                    postStatus("\n.rpa / ddlc-win.zip в Documents нет.");
                    reportArchiveStatus();
                }
                return;
            }
            int ok = 0;
            for (int i = 0; i < found.size(); i++) {
                File file = found.get(i);
                String lower = file.getName().toLowerCase(Locale.US);
                if (lower.endsWith(".zip")) {
                    if (quiet && archivesReady()) {
                        continue;
                    }
                    if (installDdlcZip(file)) {
                        ok++;
                    }
                } else if (unpackRpaFile(file)) {
                    ok++;
                }
            }
            cleanupAfterUnpack();
            postStatus("\nраспаковано архивов: " + ok);
            if (!quiet) {
                reportArchiveStatus();
            }
        } finally {
            downloadRunning = false;
        }
    }

    private void addRpaFiles(List<File> out, File dir) {
        if (dir == null || !dir.isDirectory()) {
            return;
        }
        File[] files = dir.listFiles();
        if (files == null) {
            return;
        }
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null || !file.isFile()) {
                continue;
            }
            String name = file.getName();
            if (name == null) {
                continue;
            }
            String lower = name.toLowerCase(Locale.US);
            if (lower.endsWith(".rpa") && RpaExtractor.isRpa(file) && !out.contains(file)) {
                out.add(file);
            }
        }
    }

    private void addDdlcZips(List<File> out, File dir) {
        if (dir == null || !dir.isDirectory()) {
            return;
        }
        File[] files = dir.listFiles();
        if (files == null) {
            return;
        }
        for (int i = 0; i < files.length; i++) {
            File file = files[i];
            if (file == null || !file.isFile()) {
                continue;
            }
            String name = file.getName();
            if (name == null) {
                continue;
            }
            if (name.toLowerCase(Locale.US).endsWith(".zip") && zipLooksLikeDdlc(file) && !out.contains(file)) {
                out.add(file);
            }
        }
    }

    private boolean officialRpasOnOverlay() {
        return archivesReady();
    }

    private void cleanupAfterUnpack() {
        if (gameOverlayDir != null) {
            touchNomedia(gameOverlayDir);
            touchNomedia(new File(gameOverlayDir, "images"));
            touchNomedia(new File(gameOverlayDir, "bgm"));
            touchNomedia(new File(gameOverlayDir, "sfx"));
            if (new File(gameOverlayDir, "images/bg/bedroom.png").isFile()) {
                deleteIfFile(new File(gameOverlayDir, "images.rpa"));
            }
            if (new File(gameOverlayDir, "bgm/1.ogg").isFile()) {
                deleteIfFile(new File(gameOverlayDir, "audio.rpa"));
            }
        }
        if (archivesDir != null) {
            touchNomedia(archivesDir);
            File stash = new File(archivesDir, "ddlc");
            if (stash.isDirectory() && archivesReady()) {
                deleteTree(stash);
                postStatus("\nвременная archives/ddlc убрана — файлы уже в game/");
            }
        }
        if (sideloadDir != null) {
            touchNomedia(sideloadDir);
        }
    }

    private void deleteIfFile(File file) {
        if (file != null && file.isFile() && file.delete()) {
            logLine("removed " + file.getAbsolutePath());
        }
    }

    private void deleteTree(File dir) {
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
                } else if (file.delete()) {
                    logLine("removed " + file.getAbsolutePath());
                }
            }
        }
        if (!dir.delete()) {
            logLine("keep dir " + dir.getAbsolutePath());
        }
    }

    private void runHealthReport(boolean verbose) {
        String report = healthReport();
        if (verbose) {
            postStatus("\n" + report);
        }
        logLine(report.replace('\n', ' '));
    }

    private String healthReport() {
        StringBuilder out = new StringBuilder();
        out.append("Проверка диска:");
        out.append("\nдоступ ко всем файлам: ").append(canUseDocuments() ? "да" : "нет");
        out.append("\nDocuments: ").append(sideloadDir == null ? "(нет)" : sideloadDir.getAbsolutePath());
        boolean writable = false;
        if (sideloadDir != null && (sideloadDir.isDirectory() || sideloadDir.mkdirs())) {
            File probe = new File(sideloadDir, ".write_test");
            FileOutputStream test = null;
            try {
                test = new FileOutputStream(probe);
                test.write(49);
                writable = true;
            } catch (Exception e) {
                writable = false;
            } finally {
                closeQuietly(test);
                if (probe.isFile()) {
                    probe.delete();
                }
            }
        }
        out.append("\nзапись в Documents: ").append(writable ? "да" : "нет");
        File docsFlag = new File(getFilesDir(), DOCS_FLAG);
        out.append("\nфлаг Documents: ").append(docsFlag.isFile() ? "да" : "нет");
        File[] tree = userTree();
        int missingDirs = 0;
        for (int i = 0; i < tree.length; i++) {
            File dir = tree[i];
            if (dir == null) {
                continue;
            }
            if (!dir.isDirectory()) {
                missingDirs++;
                out.append("\nнет папки ").append(dir.getName());
            }
        }
        if (missingDirs == 0) {
            out.append("\nпапки: все на месте");
        }
        boolean images = gameOverlayDir != null
                && new File(gameOverlayDir, "images/bg/bedroom.png").isFile();
        boolean audio = gameOverlayDir != null
                && new File(gameOverlayDir, "bgm/1.ogg").isFile();
        out.append("\nкартинки DDLC: ").append(images ? "да" : "нет (images/bg/bedroom.png)");
        out.append("\nмузыка DDLC: ").append(audio ? "да" : "нет (bgm/1.ogg)");
        File zip = archivesDir == null ? null : new File(archivesDir, ddlcZipName());
        out.append("\nzip ddlc: ").append(zip != null && zip.isFile() ? "есть в _mas/archives/" : "нет");
        if (archivesReady()) {
            out.append("\nархивы готовы, можно запускать MAS");
        } else {
            out.append("\nархивы не готовы — скачай ddlc.moe или положи zip в _mas/archives");
        }
        return out.toString();
    }

    private boolean unpackRpaFile(File zip) {
        return unpackRpaFile(zip, true);
    }

    private boolean unpackRpaFile(File zip, boolean keepInArchives) {
        if (zip == null || !zip.isFile()) {
            return false;
        }
        if (!RpaExtractor.isRpa(zip)) {
            postStatus("\n" + zip.getName() + " не RPA-3.0");
            return false;
        }
        if (gameOverlayDir == null || (!gameOverlayDir.isDirectory() && !gameOverlayDir.mkdirs())) {
            postStatus("\nНет папки game для распаковки.");
            return false;
        }
        postStatus("\nраспаковка " + zip.getName());
        logLine("unpack " + zip.getAbsolutePath());
        final int[] skipped = new int[] { 0 };
        try {
            int count = RpaExtractor.extract(zip, gameOverlayDir, new RpaExtractor.Progress() {
                private long lastUi = 0;

                @Override
                public void onProgress(int done, int total, String name) {
                    long now = System.currentTimeMillis();
                    if (now - lastUi < 200 && done < total) {
                        return;
                    }
                    lastUi = now;
                    final int pct = total > 0 ? (done * 100) / total : 0;
                    final String line = "распаковка " + done + " / " + total + "  " + pct + "%  " + name;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            if (progressLine != null) {
                                progressLine.setText(line);
                            }
                            if (progressBar != null) {
                                progressBar.setIndeterminate(false);
                                progressBar.setMax(100);
                                progressBar.setProgress(pct > 100 ? 100 : pct);
                            }
                            pushWebProgress(line, pct);
                        }
                    });
                }
            }, new RpaExtractor.Skip() {
                @Override
                public boolean skip(String relativePath) {
                    if (apkHasRelative(relativePath)) {
                        skipped[0]++;
                        return true;
                    }
                    if (gameOverlayDir != null && new File(gameOverlayDir, relativePath).isFile()) {
                        skipped[0]++;
                        return true;
                    }
                    return false;
                }
            });
            postStatus("\n" + zip.getName() + ": файлов " + count);
            if (skipped[0] > 0) {
                postStatus("\nпропущено (уже есть в APK или overlay): " + skipped[0]);
            }
            logLine("unpacked " + zip.getName() + " files " + count);
            if (keepInArchives && archivesDir != null && zip.getParentFile() != null
                    && !archivesDir.getAbsolutePath().equals(zip.getParentFile().getAbsolutePath())) {
                File keep = new File(archivesDir, zip.getName());
                if (!keep.getAbsolutePath().equals(zip.getAbsolutePath())) {
                    copyFile(zip, keep);
                }
            }
            return count > 0 || skipped[0] > 0;
        } catch (Exception e) {
            postStatus("\nНе удалось распаковать " + zip.getName() + ": " + messageOf(e));
            logLine("unpack failed " + messageOf(e));
            return false;
        }
    }

    private void copyFile(File src, File dest) {
        if (src == null || dest == null || src.getAbsolutePath().equals(dest.getAbsolutePath())) {
            return;
        }
        FileInputStream in = null;
        try {
            in = new FileInputStream(src);
            writeStream(in, dest);
        } catch (Exception e) {
            logLine("copy archive failed " + messageOf(e));
        }
    }

    private void pickArchive() {
        try {
            Intent intent = new Intent(Intent.ACTION_GET_CONTENT);
            intent.setType("*/*");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(Intent.createChooser(intent, "Архив DDLC (.rpa / .zip)"), REQ_PICK_RPA);
        } catch (Exception e) {
            appendStatus("\nПикер не открылся: " + messageOf(e));
        }
    }

    private void copyPickedArchive(Uri uri) {
        if (archivesDir == null) {
            resolvePaths();
        }
        if (!archivesDir.isDirectory() && !archivesDir.mkdirs()) {
            appendStatus("\nНет папки archives.");
            return;
        }
        String name = displayName(uri);
        if (name == null || name.length() == 0) {
            name = "picked.rpa";
        }
        String lower = name.toLowerCase(Locale.US);
        boolean zip = lower.endsWith(".zip");
        if (!zip && !lower.endsWith(".rpa")) {
            name = name + ".rpa";
        }
        final File dest = new File(archivesDir, name);
        final boolean fromZip = zip;
        try {
            InputStream in = getContentResolver().openInputStream(uri);
            if (!writeStream(in, dest)) {
                appendStatus("\nНе удалось скопировать архив.");
                return;
            }
        } catch (Exception e) {
            appendStatus("\nНе удалось скопировать архив: " + messageOf(e));
            return;
        }
        appendStatus("\nархив скопирован: " + dest.getAbsolutePath());
        new Thread(new Runnable() {
            @Override
            public void run() {
                if (fromZip) {
                    installDdlcZip(dest);
                } else {
                    unpackRpaFile(dest);
                }
                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {
                        pushStatusToPage();
                    }
                });
            }
        }).start();
    }

    private void startGame() {
        if (!canUseDocuments()) {
            hidingForGame = false;
            pendingOpen = "files";
            ensureBiosUi();
            appendStatus("\nНет доступа ко всем файлам. MAS пишет только в Documents/Monika_after_story.");
            appendStatus("\nОткрой настройки, включи доступ, вернись в BIOS.");
            if (webView != null && pageReady) {
                evalJs("biosOpen", "files");
            }
            pushStatusToPage();
            return;
        }
        ensureDocumentsFlag();
        ensureLayout();
        if (!archivesReady()) {
            pendingOpen = "archives";
            hidingForGame = false;
            ensureBiosUi();
            appendStatus("\nСначала поставь архивы картинок и музыки.");
            appendStatus("\nСкачай с ddlc.moe / GitHub или положи .rpa / ddlc-win.zip в Documents/Monika_after_story/_mas/archives");
            runHealthReport(true);
            if (webView != null && pageReady) {
                evalJs("biosOpen", "archives");
            }
            pushStatusToPage();
            return;
        }
        installNativeEngine();
        installMbaseFile();
        stopStockfish();
        try {
            Intent intent = new Intent(this, PythonSDLActivity.class);
            startActivity(intent);
            logLine("start PythonSDLActivity");
        } catch (Exception e) {
            appendStatus("\nНе удалось запустить игру: " + messageOf(e));
        }
    }

    private void toggleBootFlag() {
        if (flagExists("boot_renpy")) {
            deleteFlag("boot_renpy");
            appendStatus("\nСразу MAS OS: выключено. Следующий холодный старт откроет BIOS.");
        } else {
            writeFlag("boot_renpy");
            appendStatus("\nСразу MAS OS: включено. Холодный старт пропустит BIOS.");
        }
        pushStatusToPage();
    }

    private void testNativeEngine() {
        runEngineJob(new Runnable() {
            @Override
            public void run() {
                File binary = resolveEngineBinary("libhello_engine.so", "hello_engine");
                if (!binary.isFile()) {
                    installNativeEngine();
                    binary = resolveEngineBinary("libhello_engine.so", "hello_engine");
                }
                if (!binary.isFile()) {
                    postStatus("\nhello_engine нет ни в libdir, ни в files.");
                    return;
                }
                maybeChmodEngine(binary);
                postStatus("\nзапуск " + describeFile(binary));
                postStatus("\n" + execOnce(new String[] { binary.getAbsolutePath() }, 3000));
            }
        });
    }

    private void testStockfishBinary() {
        runStockfishTalk("uci", "uciok", 5000);
    }

    private void runStockfishTalk(final String cmd, final String waitFor, final int timeoutMs) {
        runEngineJob(new Runnable() {
            @Override
            public void run() {
                postStatus("\n→ " + cmd.replace("\n", " | "));
                String reply = talkStockfish(cmd, waitFor, timeoutMs);
                if (reply == null || reply.length() == 0) {
                    postStatus("\nStockfish молчит.");
                } else {
                    postStatus("\n" + reply.trim());
                }
            }
        });
    }

    private void runEngineJob(final Runnable job) {
        if (engineBusy) {
            appendStatus("\nДвижок ещё отвечает, подожди.");
            return;
        }
        engineBusy = true;
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    job.run();
                } catch (Exception e) {
                    postStatus("\nДвижок: " + messageOf(e));
                    logLine("engine job " + messageOf(e));
                } finally {
                    engineBusy = false;
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            pushStatusToPage();
                        }
                    });
                }
            }
        }).start();
    }

    private String execOnce(String[] cmd, int timeoutMs) {
        Process proc = null;
        BufferedReader reader = null;
        try {
            ProcessBuilder pb = new ProcessBuilder(cmd);
            pb.redirectErrorStream(true);
            pb.directory(getFilesDir());
            proc = pb.start();
            reader = new BufferedReader(new InputStreamReader(proc.getInputStream(), "UTF-8"));
            StringBuilder out = new StringBuilder();
            long deadline = System.currentTimeMillis() + timeoutMs;
            while (System.currentTimeMillis() < deadline) {
                while (reader.ready()) {
                    String line = reader.readLine();
                    if (line == null) {
                        deadline = 0;
                        break;
                    }
                    if (out.length() > 0) {
                        out.append("\n");
                    }
                    out.append(line);
                    logLine("engine << " + line);
                }
                try {
                    proc.exitValue();
                    break;
                } catch (IllegalThreadStateException running) {
                    Thread.sleep(30);
                }
            }
            if (out.length() == 0) {
                return "процесс ничего не напечатал за " + timeoutMs + " мс";
            }
            return out.toString();
        } catch (Exception e) {
            return "ошибка: " + messageOf(e);
        } finally {
            if (reader != null) {
                try {
                    reader.close();
                } catch (Exception ignored) {
                }
            }
            if (proc != null) {
                try {
                    proc.destroy();
                } catch (Exception ignored) {
                }
            }
        }
    }

    private String talkStockfish(String cmd, String waitFor, int timeoutMs) {
        try {
            ensureStockfishProcess();
            String payload = cmd.endsWith("\n") ? cmd : cmd + "\n";
            synchronized (this) {
                stockfishStdin.write(payload.getBytes("UTF-8"));
                stockfishStdin.flush();
            }
            logLine("sf >> " + cmd.replace("\n", " | "));
            return readStockfishUntil(waitFor, timeoutMs);
        } catch (Exception e) {
            logLine("sf talk failed " + messageOf(e));
            stopStockfish();
            return "ошибка: " + messageOf(e);
        }
    }

    private void ensureStockfishProcess() throws Exception {
        synchronized (this) {
            if (stockfishProc != null) {
                try {
                    stockfishProc.exitValue();
                    stockfishProc = null;
                } catch (IllegalThreadStateException stillRunning) {
                    return;
                }
            }
            File bin = resolveEngineBinary("libstockfish.so", "stockfish");
            if (!bin.isFile()) {
                installNativeEngine();
                bin = resolveEngineBinary("libstockfish.so", "stockfish");
            }
            if (!bin.isFile()) {
                throw new IOException("нет libstockfish.so — пересобери APK (jniLibs) и нажми «Проверить ELF»");
            }
            maybeChmodEngine(bin);
            ProcessBuilder pb = new ProcessBuilder(bin.getAbsolutePath());
            pb.redirectErrorStream(true);
            pb.directory(getFilesDir());
            stockfishProc = pb.start();
            stockfishStdin = stockfishProc.getOutputStream();
            stockfishRaw = stockfishProc.getInputStream();
            stockfishReader = new BufferedReader(
                    new InputStreamReader(stockfishRaw, "UTF-8"));
            logLine("stockfish started " + bin.getAbsolutePath());
        }
    }

    private boolean stockfishHasLine() throws IOException {
        if (stockfishReader != null && stockfishReader.ready()) {
            return true;
        }
        if (stockfishRaw != null && stockfishRaw.available() > 0) {
            return true;
        }
        return false;
    }

    private String readStockfishUntil(String token, int timeoutMs) throws Exception {
        StringBuilder out = new StringBuilder();
        long deadline = System.currentTimeMillis() + timeoutMs;
        boolean saw = token == null || token.length() == 0;
        while (System.currentTimeMillis() < deadline) {
            boolean progressed = false;
            while (stockfishReader != null && stockfishHasLine()) {
                String line = stockfishReader.readLine();
                if (line == null) {
                    deadline = 0;
                    break;
                }
                progressed = true;
                if (out.length() > 0) {
                    out.append("\n");
                }
                out.append(line);
                logLine("sf << " + line);
                if (token != null && line.indexOf(token) >= 0) {
                    saw = true;
                    deadline = 0;
                    break;
                }
            }
            if (deadline == 0) {
                break;
            }
            if (!progressed) {
                Thread.sleep(30);
            }
        }
        if (out.length() == 0) {
            return "(тишина " + timeoutMs + " мс)";
        }
        if (!saw && token != null) {
            out.append("\n(нет «").append(token).append("» за ").append(timeoutMs).append(" мс)");
        }
        return out.toString();
    }

    private void stopStockfish() {
        synchronized (this) {
            if (stockfishStdin != null) {
                try {
                    stockfishStdin.write("quit\n".getBytes("UTF-8"));
                    stockfishStdin.flush();
                } catch (Exception ignored) {
                }
            }
            if (stockfishReader != null) {
                try {
                    stockfishReader.close();
                } catch (Exception ignored) {
                }
                stockfishReader = null;
            }
            stockfishRaw = null;
            if (stockfishStdin != null) {
                try {
                    stockfishStdin.close();
                } catch (Exception ignored) {
                }
                stockfishStdin = null;
            }
            if (stockfishProc != null) {
                try {
                    stockfishProc.destroy();
                } catch (Exception ignored) {
                }
                stockfishProc = null;
            }
        }
    }

    private void showTraceback() {
        File file = findTraceback();
        if (file == null) {
            String msg = "traceback.txt не найден.\n"
                    + "Искал в Documents/Monika_after_story/_mas/log и в files приложения.\n"
                    + "После краша Ren'Py файл появится сам — открой эту кнопку снова.";
            evalJs("biosTrace", msg);
            appendStatus("\ntraceback.txt нет");
            return;
        }
        String body = readTextTail(file, 96 * 1024);
        if (body == null || body.length() == 0) {
            evalJs("biosTrace", "traceback.txt пустой: " + file.getAbsolutePath());
            appendStatus("\ntraceback.txt пустой");
            return;
        }
        evalJs("biosTrace", file.getAbsolutePath() + "\n\n" + body);
        appendStatus("\nоткрыт traceback: " + file.getAbsolutePath());
    }

    private File findTraceback() {
        List<File> places = new ArrayList<File>();
        if (sideloadDir != null) {
            places.add(new File(new File(masDir(), "log"), "traceback.txt"));
            places.add(new File(sideloadDir, "traceback.txt"));
        }
        if (gameOverlayDir != null && gameOverlayDir.getParentFile() != null) {
            places.add(new File(gameOverlayDir.getParentFile(), "traceback.txt"));
        }
        places.add(new File(getFilesDir(), "traceback.txt"));
        if (logFile != null && logFile.getParentFile() != null) {
            places.add(new File(logFile.getParentFile(), "traceback.txt"));
        }
        try {
            File ext = Environment.getExternalStorageDirectory();
            if (ext != null) {
                places.add(new File(new File(new File(ext, "Documents"), "Monika_after_story"), "traceback.txt"));
            }
        } catch (Exception ignored) {
        }
        File best = null;
        long bestTime = -1L;
        for (int i = 0; i < places.size(); i++) {
            File file = places.get(i);
            if (file == null || !file.isFile() || file.length() <= 0) {
                continue;
            }
            long when = file.lastModified();
            if (best == null || when > bestTime) {
                best = file;
                bestTime = when;
            }
        }
        return best;
    }

    private String readTextTail(File file, int maxBytes) {
        if (file == null || !file.isFile()) {
            return null;
        }
        FileInputStream in = null;
        try {
            long size = file.length();
            in = new FileInputStream(file);
            if (size > maxBytes) {
                long skip = size - maxBytes;
                while (skip > 0) {
                    long n = in.skip(skip);
                    if (n <= 0) {
                        break;
                    }
                    skip -= n;
                }
            }
            byte[] buf = new byte[Math.min(maxBytes, (int) Math.max(size, 1))];
            int got = 0;
            int n;
            while (got < buf.length && (n = in.read(buf, got, buf.length - got)) >= 0) {
                if (n > 0) {
                    got += n;
                }
            }
            String text = new String(buf, 0, got, "UTF-8");
            if (size > maxBytes) {
                return "...(обрезано, показан хвост)\n" + text;
            }
            return text;
        } catch (Exception e) {
            return "не прочитался: " + messageOf(e);
        } finally {
            closeQuietly(in);
        }
    }

    private void shareLauncherLog() {
        if (logFile == null || !logFile.isFile()) {
            appendStatus("\nЛога ещё нет.");
            return;
        }
        File local = new File(getFilesDir(), "launcher.log");
        try {
            FileInputStream in = new FileInputStream(logFile);
            if (!writeStream(in, local)) {
                appendStatus("\nНе удалось скопировать лог в files.");
                return;
            }
            String authority = getPackageName() + ".fileprovider";
            Uri uri = FileProvider.getUriForFile(this, authority, local);
            Intent send = new Intent(Intent.ACTION_SEND);
            send.setType("text/plain");
            send.putExtra(Intent.EXTRA_STREAM, uri);
            send.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            startActivity(Intent.createChooser(send, "Лог BIOS"));
        } catch (Exception e) {
            appendStatus("\nЛог не отправился: " + messageOf(e));
        }
    }

    private void openAllFilesSettings() {
        try {
            Intent intent = new Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION);
            intent.setData(Uri.parse("package:" + getPackageName()));
            startActivity(intent);
        } catch (Exception e) {
            try {
                startActivity(new Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION));
            } catch (Exception e2) {
                appendStatus("\nНе удалось открыть настройки: " + messageOf(e2));
            }
        }
    }

    private void logLine(String message) {
        if (logFile == null) {
            return;
        }
        FileWriter writer = null;
        try {
            File parent = logFile.getParentFile();
            if (parent != null && !parent.isDirectory()) {
                parent.mkdirs();
            }
            String stamp = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.US).format(new Date());
            writer = new FileWriter(logFile, true);
            writer.write(stamp);
            writer.write(" ");
            writer.write(message);
            writer.write("\n");
        } catch (Exception ignored) {
        } finally {
            if (writer != null) {
                try {
                    writer.close();
                } catch (IOException ignored) {
                }
            }
        }
    }

    private static final String[] BIOS_PAGE_NAMES = new String[] {
            "index.html", "styles.css", "app.js"
    };

    private File prepareBiosWww() {
        biosPrepareAttempted = true;
        File dir = new File(getFilesDir(), "bios_www");
        if (!dir.isDirectory() && !dir.mkdirs()) {
            logLine("bios www mkdir failed " + dir.getAbsolutePath());
        }
        // Игровые assets с префиксом x- не читаем: Ren'Py так пакует game/.
        if (copyAssetWww(dir)) {
            biosByteSource = "android_asset/www";
        } else if (copySideloadWww(dir)) {
            biosByteSource = "Documents/Monika_after_story/bios_www";
        } else if (copyRawWww(dir)) {
            biosByteSource = "R.raw bios_index.html bios_styles.css bios_app.js";
        } else {
            biosByteSource = "none";
        }
        copyOptionalArchivesJson(dir);
        logBiosFiles();
        return new File(dir, "index.html");
    }

    private void logBiosFiles() {
        File dir = new File(getFilesDir(), "bios_www");
        for (int i = 0; i < BIOS_PAGE_NAMES.length; i++) {
            File file = new File(dir, BIOS_PAGE_NAMES[i]);
            logLine("bios file " + file.getAbsolutePath()
                    + " exists=" + file.isFile()
                    + " source=" + biosByteSource);
        }
    }

    private boolean copyAssetWww(File dir) {
        for (int i = 0; i < BIOS_PAGE_NAMES.length; i++) {
            InputStream in = null;
            try {
                in = getAssets().open("www/" + BIOS_PAGE_NAMES[i]);
            } catch (IOException e) {
                closeQuietly(in);
                return false;
            }
            if (!writeStream(in, new File(dir, BIOS_PAGE_NAMES[i]))) {
                return false;
            }
        }
        return new File(dir, "index.html").isFile();
    }

    private boolean copySideloadWww(File dir) {
        if (sideloadDir == null) {
            return false;
        }
        File src = new File(sideloadDir, "bios_www");
        if (!new File(src, "index.html").isFile()) {
            return false;
        }
        try {
            for (int i = 0; i < BIOS_PAGE_NAMES.length; i++) {
                File from = new File(src, BIOS_PAGE_NAMES[i]);
                if (!from.isFile()) {
                    return false;
                }
                FileInputStream in = new FileInputStream(from);
                if (!writeStream(in, new File(dir, BIOS_PAGE_NAMES[i]))) {
                    return false;
                }
            }
        } catch (IOException e) {
            return false;
        }
        return new File(dir, "index.html").isFile();
    }

    private boolean copyRawWww(File dir) {
        int[] ids = new int[] { R.raw.bios_index, R.raw.bios_styles, R.raw.bios_app };
        try {
            for (int i = 0; i < ids.length; i++) {
                InputStream in = getResources().openRawResource(ids[i]);
                if (!writeStream(in, new File(dir, BIOS_PAGE_NAMES[i]))) {
                    return false;
                }
            }
        } catch (Exception e) {
            logLine("bios raw failed " + messageOf(e));
            return false;
        }
        return new File(dir, "index.html").isFile();
    }

    private void copyOptionalArchivesJson(File dir) {
        File dest = new File(dir, "archives.json");
        try {
            InputStream in = getAssets().open("www/archives.json");
            if (writeStream(in, dest)) {
                return;
            }
        } catch (Exception ignored) {
        }
        try {
            InputStream in = getResources().openRawResource(R.raw.bios_archives);
            if (writeStream(in, dest)) {
                return;
            }
        } catch (Exception ignored) {
        }
        if (sideloadDir != null) {
            File from = new File(new File(sideloadDir, "bios_www"), "archives.json");
            if (from.isFile()) {
                try {
                    writeStream(new FileInputStream(from), dest);
                } catch (Exception ignored) {
                }
            }
        }
    }

    private boolean writeStream(InputStream in, File dest) {
        FileOutputStream out = null;
        try {
            if (in == null) {
                return false;
            }
            out = new FileOutputStream(dest);
            byte[] buf = new byte[8192];
            int n;
            while ((n = in.read(buf)) >= 0) {
                if (n > 0) {
                    out.write(buf, 0, n);
                }
            }
            out.flush();
            return dest.isFile();
        } catch (IOException e) {
            return false;
        } finally {
            closeQuietly(in);
            closeQuietly(out);
        }
    }

    private void closeQuietly(java.io.Closeable stream) {
        if (stream == null) {
            return;
        }
        try {
            stream.close();
        } catch (IOException ignored) {
        }
    }

    private boolean tryShowWebBios() {
        File index = prepareBiosWww();
        boolean exists = index != null && index.isFile();
        String path = index == null ? "(нет пути)" : index.getAbsolutePath();
        logLine("bios html " + path + " exists=" + exists);
        if (!exists) {
            return false;
        }
        String pageUrl = Uri.fromFile(index).toString();
        logLine("bios load " + pageUrl);
        try {
            WebView web = new WebView(this);
            WebSettings settings = web.getSettings();
            settings.setJavaScriptEnabled(true);
            settings.setAllowFileAccess(true);
            settings.setAllowFileAccessFromFileURLs(true);
            settings.setAllowUniversalAccessFromFileURLs(true);
            settings.setDomStorageEnabled(false);
            settings.setSupportZoom(false);
            settings.setUseWideViewPort(true);
            settings.setLoadWithOverviewMode(false);
            web.setWebViewClient(new WebViewClient() {
                @Override
                public boolean shouldOverrideUrlLoading(WebView view, String url) {
                    if (url != null && url.indexOf('#') >= 0) {
                        return true;
                    }
                    return false;
                }

                @Override
                public boolean shouldOverrideUrlLoading(WebView view, android.webkit.WebResourceRequest request) {
                    if (request == null || request.getUrl() == null) {
                        return false;
                    }
                    return shouldOverrideUrlLoading(view, request.getUrl().toString());
                }

                @Override
                public void onPageFinished(WebView view, String url) {
                    pageReady = true;
                    flushWebBuffer();
                    evalJs("biosSetView", biosViewName());
                    evalJs("biosSubmods", SubmodInstaller.listJson(sideloadDir));
                    if (!pageOpened) {
                        pageOpened = true;
                        if (pendingOpen != null && pendingOpen.length() > 0) {
                            evalJs("biosOpen", pendingOpen);
                        }
                    }
                    pushStatusToPage();
                }

                @Override
                public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                    if (failingUrl != null && failingUrl.indexOf("index.html") >= 0) {
                        showWebFailed(String.valueOf(errorCode), failingUrl);
                    }
                }

                @Override
                public void onReceivedError(WebView view, android.webkit.WebResourceRequest request, android.webkit.WebResourceError error) {
                    if (request != null && request.isForMainFrame()) {
                        String url = request.getUrl() == null ? "" : request.getUrl().toString();
                        int code = error == null ? -1 : error.getErrorCode();
                        showWebFailed(String.valueOf(code), url);
                    }
                }
            });
            web.addJavascriptInterface(new BiosBridge(), "BiosBridge");
            web.loadUrl(pageUrl);
            webView = web;
            setContentView(web);
            return true;
        } catch (Throwable t) {
            webView = null;
            showWebFailed(messageOf(t), pageUrl);
            return true;
        }
    }

    private void showNativeBios() {
        if (nativeShown) {
            return;
        }
        nativeShown = true;
        pageReady = false;
        webView = null;
        setContentView(R.layout.activity_launcher);
        pathView = (TextView) findViewById(R.id.bios_path);
        statusView = (TextView) findViewById(R.id.bios_log);
        progressBar = (ProgressBar) findViewById(R.id.bios_progress);
        progressLine = (TextView) findViewById(R.id.bios_progress_line);
        findViewById(R.id.bios_export_saves).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                exportSaves();
            }
        });
        findViewById(R.id.bios_import_saves).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                importSaves();
            }
        });
        findViewById(R.id.bios_share_saves).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                shareSaves();
            }
        });
        findViewById(R.id.bios_update_check).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                checkUpdate();
            }
        });
        findViewById(R.id.bios_update_install).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                downloadUpdate();
            }
        });
        findViewById(R.id.bios_pick_image).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                pickImage();
            }
        });
        findViewById(R.id.bios_pick_zip).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                pickSubmodArchive();
            }
        });
        findViewById(R.id.bios_html).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                useHtmlUi();
            }
        });
        findViewById(R.id.bios_start).setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                startGame();
            }
        });
    }

    private File flagFile(String name) {
        if (sideloadDir == null) {
            resolvePaths();
        }
        return new File(flagsDir(), name);
    }

    private boolean flagExists(String name) {
        try {
            if (flagFile(name).isFile()) {
                return true;
            }
            if (sideloadDir != null) {
                if (new File(new File(sideloadDir, "flags"), name).isFile()) {
                    return true;
                }
                if (new File(sideloadDir, name).isFile()) {
                    return true;
                }
            }
            return false;
        } catch (Exception e) {
            return false;
        }
    }

    private void writeSafeModeFlag() {
        // Ren'Py basedir on Android is getFilesDir(); 0config reads mas_os_safe_mode there.
        writeOneShot(new File(getFilesDir(), "mas_os_safe_mode"));
        writeOneShot(new File(flagsDir(), "mas_os_safe_mode"));
    }

    private void writeOneShot(File file) {
        FileOutputStream out = null;
        try {
            File dir = file.getParentFile();
            if (dir != null && !dir.isDirectory()) {
                dir.mkdirs();
            }
            out = new FileOutputStream(file);
            out.write("1\n".getBytes("UTF-8"));
            logLine("wrote " + file.getAbsolutePath());
        } catch (Exception e) {
            logLine("safe mode failed " + file.getAbsolutePath() + " " + messageOf(e));
        } finally {
            closeQuietly(out);
        }
    }

    private void writeFlag(String name) {
        try {
            File file = flagFile(name);
            File dir = file.getParentFile();
            if (dir != null && !dir.isDirectory()) {
                dir.mkdirs();
            }
            FileOutputStream out = new FileOutputStream(file);
            try {
                out.write("1\n".getBytes("UTF-8"));
            } finally {
                out.close();
            }
            logLine("flag set " + file.getAbsolutePath());
        } catch (Exception e) {
            logLine("flag set failed " + name + " " + messageOf(e));
        }
    }

    private void deleteFlag(String name) {
        try {
            File file = flagFile(name);
            if (file.exists() && file.delete()) {
                logLine("flag cleared " + file.getAbsolutePath());
            }
        } catch (Exception e) {
            logLine("flag clear failed " + name + " " + messageOf(e));
        }
    }

    private void useNativeUi() {
        writeFlag("ui_native");
        nativeShown = false;
        showNativeBios();
        appendStatus("\nСтарый интерфейс");
    }

    private void useHtmlUi() {
        deleteFlag("ui_native");
        nativeShown = false;
        statusView = null;
        if (!tryShowWebBios()) {
            File missing = new File(new File(getFilesDir(), "bios_www"), "index.html");
            showWebFailed("exists=false", missing.getAbsolutePath());
        }
    }

    private void showWebFailed(String code, String url) {
        logLine("webview error code " + code + " url " + url);
        pageReady = false;
        webView = null;
        nativeShown = false;
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setBackgroundColor(0xFF1a1420);
        box.setPadding(32, 32, 32, 32);
        TextView title = new TextView(this);
        title.setText("WebView не открылся");
        title.setTextColor(0xFFf4e9f2);
        title.setTextSize(20);
        TextView detail = new TextView(this);
        detail.setText("код " + code + "\n" + url);
        detail.setTextColor(0xFF7ee0d6);
        Button button = new Button(this);
        button.setText("Старый интерфейс");
        button.setOnClickListener(new View.OnClickListener() {
            @Override
            public void onClick(View v) {
                useNativeUi();
            }
        });
        box.addView(title);
        box.addView(detail);
        box.addView(button);
        setContentView(box);
    }

    private void pushWebLog(String text) {
        if (text == null) {
            return;
        }
        if (webView == null || !pageReady) {
            webBuffer.append(text);
            return;
        }
        evalJs("biosLog", text);
    }

    private void flushWebBuffer() {
        if (webBuffer.length() == 0) {
            return;
        }
        String text = webBuffer.toString();
        webBuffer.setLength(0);
        evalJs("biosLog", text);
    }

    private void pushStatusToPage() {
        String path = sideloadDir == null ? "" : sideloadDir.getAbsolutePath();
        String version = currentVersionName();
        boolean filesOk = canUseDocuments();
        boolean engineOk = nativeSo("libstockfish.so").isFile()
                || nativeSo("libhello_engine.so").isFile()
                || new File(getFilesDir(), "stockfish").isFile()
                || new File(getFilesDir(), "hello_engine").isFile();
        boolean skip = flagExists("boot_renpy");
        boolean archivesOk = archivesReady();
        boolean tracebackOk = findTraceback() != null;
        String js = "if(window.biosSetStatus){biosSetStatus({path:" + jsString(path)
                + ",version:" + jsString(version)
                + ",filesOk:" + (filesOk ? "true" : "false")
                + ",engineOk:" + (engineOk ? "true" : "false")
                + ",skipBios:" + (skip ? "true" : "false")
                + ",archivesOk:" + (archivesOk ? "true" : "false")
                + ",tracebackOk:" + (tracebackOk ? "true" : "false")
                + "});}";
        evalRaw(js);
    }

    private void evalRaw(final String js) {
        if (webView == null) {
            return;
        }
        webView.post(new Runnable() {
            @Override
            public void run() {
                if (webView == null) {
                    return;
                }
                if (Build.VERSION.SDK_INT >= 19) {
                    webView.evaluateJavascript(js, null);
                } else {
                    webView.loadUrl("javascript:" + js);
                }
            }
        });
    }

    private static final int URL_HISTORY_MAX = 24;

    private JSONArray loadUrlHistory() {
        String raw = getSharedPreferences("mas_bios", MODE_PRIVATE)
                .getString("url_history", "[]");
        try {
            JSONArray arr = new JSONArray(raw == null ? "[]" : raw);
            return arr;
        } catch (Exception e) {
            return new JSONArray();
        }
    }

    private void rememberUrl(String raw) {
        String url = raw == null ? "" : raw.trim();
        if (url.length() < 8) {
            return;
        }
        JSONArray old = loadUrlHistory();
        JSONArray next = new JSONArray();
        try {
            JSONObject row = new JSONObject();
            row.put("url", url);
            row.put("at", System.currentTimeMillis());
            next.put(row);
            int i;
            for (i = 0; i < old.length(); i++) {
                JSONObject other = old.optJSONObject(i);
                String u = other == null ? "" : other.optString("url", "");
                if (u.length() == 0 || url.equals(u)) {
                    continue;
                }
                next.put(other);
                if (next.length() >= URL_HISTORY_MAX) {
                    break;
                }
            }
        } catch (Exception ignored) {
        }
        getSharedPreferences("mas_bios", MODE_PRIVATE)
                .edit()
                .putString("url_history", next.toString())
                .apply();
        evalJs("biosUrlHistory", next.toString());
    }

    private void dropUrlHistory(String raw) {
        String url = raw == null ? "" : raw.trim();
        JSONArray old = loadUrlHistory();
        JSONArray next = new JSONArray();
        int i;
        for (i = 0; i < old.length(); i++) {
            JSONObject other = old.optJSONObject(i);
            String u = other == null ? "" : other.optString("url", "");
            if (u.length() == 0 || url.equals(u)) {
                continue;
            }
            next.put(other);
        }
        getSharedPreferences("mas_bios", MODE_PRIVATE)
                .edit()
                .putString("url_history", next.toString())
                .apply();
        evalJs("biosUrlHistory", next.toString());
    }

    private void evalJs(String fn, String arg) {
        if (webView == null) {
            return;
        }
        final String js = "if(window." + fn + "){window." + fn + "(" + jsString(arg) + ");}";
        webView.post(new Runnable() {
            @Override
            public void run() {
                if (webView == null) {
                    return;
                }
                if (Build.VERSION.SDK_INT >= 19) {
                    webView.evaluateJavascript(js, null);
                } else {
                    webView.loadUrl("javascript:" + js);
                }
            }
        });
    }

    private String jsString(String text) {
        StringBuilder out = new StringBuilder();
        out.append('"');
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == '\\' || c == '"') {
                out.append('\\');
                out.append(c);
            } else if (c == '\n') {
                out.append("\\n");
            } else if (c == '\r') {
                out.append("\\r");
            } else {
                out.append(c);
            }
        }
        out.append('"');
        return out.toString();
    }

    private void setStatus(String text) {
        if (statusView != null) {
            statusView.setText(text);
        }
        pushWebLog(text);
    }

    private void appendStatus(String text) {
        if (statusView != null) {
            statusView.append(text);
        }
        pushWebLog(text);
    }

    private String messageOf(Throwable t) {
        if (t == null) {
            return "";
        }
        String message = t.getMessage();
        if (message == null || message.length() == 0) {
            return t.getClass().getSimpleName();
        }
        return message;
    }
}
