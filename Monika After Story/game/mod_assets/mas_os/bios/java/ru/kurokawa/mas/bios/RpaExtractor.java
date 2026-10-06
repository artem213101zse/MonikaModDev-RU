// RPA-3.0 unpacker for MAS BIOS. Same layout as renpy.loader.RPAv3ArchiveHandler:
// header "RPA-3.0 ", hex offset + key, zlib+pickle index, data bytes as-is.
package ru.kurokawa.mas.bios;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.zip.Inflater;
import java.util.zip.InflaterInputStream;

public final class RpaExtractor {

    public interface Progress {
        void onProgress(int done, int total, String name);
    }

    public interface Skip {
        boolean skip(String relativePath);
    }

    public static final class Part {
        public final long offset;
        public final long length;
        public final byte[] start;

        Part(long offset, long length, byte[] start) {
            this.offset = offset;
            this.length = length;
            this.start = start == null ? new byte[0] : start;
        }
    }

    private RpaExtractor() {
    }

    public static boolean isRpa(File file) {
        if (file == null || !file.isFile()) {
            return false;
        }
        FileInputStream in = null;
        try {
            in = new FileInputStream(file);
            byte[] header = new byte[8];
            int n = in.read(header);
            return n == 8 && header[0] == 'R' && header[1] == 'P' && header[2] == 'A'
                    && header[3] == '-' && header[4] == '3' && header[5] == '.'
                    && header[6] == '0' && header[7] == ' ';
        } catch (IOException e) {
            return false;
        } finally {
            if (in != null) {
                try {
                    in.close();
                } catch (IOException ignored) {
                }
            }
        }
    }

    public static int extract(File archive, File destDir, Progress progress) throws IOException {
        return extract(archive, destDir, progress, null);
    }

    public static int extract(File archive, File destDir, Progress progress, Skip skip) throws IOException {
        if (archive == null || destDir == null) {
            throw new IOException("нет архива");
        }
        Map<String, List<Part>> index = readIndex(archive);
        if (!destDir.isDirectory() && !destDir.mkdirs()) {
            throw new IOException("не создана папка " + destDir.getAbsolutePath());
        }
        String root = destDir.getCanonicalPath();
        int total = index.size();
        int done = 0;
        int written = 0;
        RandomAccessFile raf = new RandomAccessFile(archive, "r");
        try {
            for (Map.Entry<String, List<Part>> entry : index.entrySet()) {
                String name = entry.getKey();
                done++;
                if (skip != null && skip.skip(name)) {
                    if (progress != null) {
                        progress.onProgress(done, total, "skip " + name);
                    }
                    continue;
                }
                File out = safeFile(destDir, name);
                String target = out.getCanonicalPath();
                if (!target.equals(root) && !target.startsWith(root + File.separator)) {
                    throw new IOException("плохой путь в архиве: " + name);
                }
                File parent = out.getParentFile();
                if (parent != null && !parent.isDirectory() && !parent.mkdirs()) {
                    throw new IOException("не создана папка " + parent.getAbsolutePath());
                }
                writeParts(raf, entry.getValue(), out);
                written++;
                if (progress != null) {
                    progress.onProgress(done, total, name);
                }
            }
        } finally {
            raf.close();
        }
        return written;
    }

    static Map<String, List<Part>> readIndex(File archive) throws IOException {
        RandomAccessFile raf = new RandomAccessFile(archive, "r");
        try {
            byte[] header = new byte[40];
            raf.readFully(header);
            String line = new String(header, "US-ASCII");
            if (!line.startsWith("RPA-3.0 ")) {
                throw new IOException("не RPA-3.0");
            }
            long indexOff;
            int key;
            try {
                indexOff = Long.parseLong(line.substring(8, 24).trim(), 16);
                key = (int) Long.parseLong(line.substring(25, 33).trim(), 16);
            } catch (Exception e) {
                throw new IOException("битый заголовок RPA");
            }
            if (indexOff < 40 || indexOff >= raf.length()) {
                throw new IOException("смещение индекса вне файла");
            }
            raf.seek(indexOff);
            long packedLen = raf.length() - indexOff;
            if (packedLen <= 0 || packedLen > 32L * 1024L * 1024L) {
                throw new IOException("индекс слишком большой");
            }
            byte[] packed = new byte[(int) packedLen];
            raf.readFully(packed);
            byte[] raw = inflate(packed);
            Object parsed = new PickleReader(raw).read();
            if (!(parsed instanceof Map)) {
                throw new IOException("индекс не словарь");
            }
            Map<?, ?> rawMap = (Map<?, ?>) parsed;
            Map<String, List<Part>> clean = new HashMap<String, List<Part>>();
            for (Map.Entry<?, ?> item : rawMap.entrySet()) {
                String name = String.valueOf(item.getKey()).replace('\\', '/');
                List<Part> parts = decodeParts(item.getValue(), key);
                if (name.length() > 0 && parts.size() > 0) {
                    clean.put(name, parts);
                }
            }
            return clean;
        } finally {
            raf.close();
        }
    }

    private static List<Part> decodeParts(Object value, int key) throws IOException {
        if (!(value instanceof List)) {
            throw new IOException("запись индекса не список");
        }
        List<Part> out = new ArrayList<Part>();
        List<?> rows = (List<?>) value;
        for (int i = 0; i < rows.size(); i++) {
            Object row = rows.get(i);
            if (!(row instanceof List)) {
                throw new IOException("кусок индекса не кортеж");
            }
            List<?> cells = (List<?>) row;
            if (cells.size() < 2) {
                throw new IOException("кусок индекса короткий");
            }
            long offset = (toLong(cells.get(0)) & 0xffffffffL) ^ (key & 0xffffffffL);
            long length = (toLong(cells.get(1)) & 0xffffffffL) ^ (key & 0xffffffffL);
            offset &= 0xffffffffL;
            length &= 0xffffffffL;
            byte[] start = new byte[0];
            if (cells.size() >= 3) {
                start = toBytes(cells.get(2));
            }
            out.add(new Part(offset, length, start));
        }
        return out;
    }

    private static long toLong(Object value) throws IOException {
        if (value instanceof Number) {
            return ((Number) value).longValue();
        }
        throw new IOException("ожидалось число");
    }

    private static byte[] toBytes(Object value) {
        if (value == null) {
            return new byte[0];
        }
        if (value instanceof byte[]) {
            return (byte[]) value;
        }
        if (value instanceof String) {
            try {
                return ((String) value).getBytes("ISO-8859-1");
            } catch (Exception e) {
                return new byte[0];
            }
        }
        return new byte[0];
    }

    private static void writeParts(RandomAccessFile raf, List<Part> parts, File out) throws IOException {
        FileOutputStream dest = new FileOutputStream(out);
        try {
            byte[] buf = new byte[64 * 1024];
            for (int i = 0; i < parts.size(); i++) {
                Part part = parts.get(i);
                if (part.length < 0) {
                    throw new IOException("отрицательная длина");
                }
                int prefix = part.start.length;
                if (prefix > part.length) {
                    prefix = (int) part.length;
                }
                if (prefix > 0) {
                    dest.write(part.start, 0, prefix);
                }
                long rest = part.length - prefix;
                raf.seek(part.offset);
                while (rest > 0) {
                    int want = rest > buf.length ? buf.length : (int) rest;
                    int n = raf.read(buf, 0, want);
                    if (n <= 0) {
                        throw new IOException("короткое чтение RPA");
                    }
                    dest.write(buf, 0, n);
                    rest -= n;
                }
            }
            dest.flush();
        } finally {
            dest.close();
        }
    }

    private static File safeFile(File destDir, String name) throws IOException {
        String relative = name.replace('\\', '/');
        if (relative.startsWith("/") || relative.indexOf(':') >= 0) {
            throw new IOException("плохой путь: " + name);
        }
        String[] bits = relative.split("/");
        File cursor = destDir;
        for (int i = 0; i < bits.length; i++) {
            String bit = bits[i];
            if (bit.length() == 0 || ".".equals(bit) || "..".equals(bit)) {
                throw new IOException("плохой путь: " + name);
            }
            cursor = new File(cursor, bit);
        }
        return cursor;
    }

    private static byte[] inflate(byte[] packed) throws IOException {
        Inflater inflater = new Inflater();
        InflaterInputStream in = new InflaterInputStream(new ByteArrayInputStream(packed), inflater);
        try {
            byte[] buf = new byte[8192];
            java.io.ByteArrayOutputStream out = new java.io.ByteArrayOutputStream();
            int n;
            while ((n = in.read(buf)) >= 0) {
                if (n > 0) {
                    out.write(buf, 0, n);
                }
                if (out.size() > 32 * 1024 * 1024) {
                    throw new IOException("индекс слишком большой");
                }
            }
            return out.toByteArray();
        } finally {
            try {
                in.close();
            } catch (IOException ignored) {
            }
            inflater.end();
        }
    }

    /**
     * Subset of Python pickle needed for RPA indexes (protocol 0-2).
     */
    static final class PickleReader {
        private static final int MARK = 0x28;
        private static final int STOP = 0x2e;
        private static final int BININT = 0x4a;
        private static final int BININT1 = 0x4b;
        private static final int BININT2 = 0x4d;
        private static final int NONE = 0x4e;
        private static final int SHORT_BINSTRING = 0x55;
        private static final int BINSTRING = 0x54;
        private static final int BINUNICODE = 0x58;
        private static final int EMPTY_LIST = 0x5d;
        private static final int APPEND = 0x61;
        private static final int BUILD = 0x62;
        private static final int APPENDS = 0x65;
        private static final int BINGET = 0x68;
        private static final int LONG_BINGET = 0x6a;
        private static final int BINPUT = 0x71;
        private static final int LONG_BINPUT = 0x72;
        private static final int SETITEM = 0x73;
        private static final int TUPLE = 0x74;
        private static final int SETITEMS = 0x75;
        private static final int EMPTY_DICT = 0x7d;
        private static final int PROTO = 0x80;
        private static final int TUPLE1 = 0x85;
        private static final int TUPLE2 = 0x86;
        private static final int TUPLE3 = 0x87;
        private static final int NEWTRUE = 0x88;
        private static final int NEWFALSE = 0x89;
        private static final int LONG1 = 0x8a;
        private static final int LONG4 = 0x8b;
        private static final int BINFLOAT = 0x47;
        private static final int EMPTY_TUPLE = 0x29;

        private final byte[] data;
        private int pos;
        private final ArrayList<Object> stack = new ArrayList<Object>();
        private final HashMap<Integer, Object> memo = new HashMap<Integer, Object>();

        PickleReader(byte[] data) {
            this.data = data;
        }

        Object read() throws IOException {
            while (pos < data.length) {
                int op = data[pos++] & 0xff;
                if (op == STOP) {
                    if (stack.isEmpty()) {
                        throw new IOException("пустой pickle");
                    }
                    return stack.get(stack.size() - 1);
                }
                step(op);
            }
            throw new IOException("pickle без STOP");
        }

        private void step(int op) throws IOException {
            switch (op) {
                case PROTO:
                    readByte();
                    return;
                case NONE:
                    stack.add(null);
                    return;
                case NEWTRUE:
                    stack.add(Boolean.TRUE);
                    return;
                case NEWFALSE:
                    stack.add(Boolean.FALSE);
                    return;
                case EMPTY_DICT:
                    stack.add(new HashMap<Object, Object>());
                    return;
                case EMPTY_LIST:
                    stack.add(new ArrayList<Object>());
                    return;
                case EMPTY_TUPLE:
                    stack.add(new ArrayList<Object>());
                    return;
                case MARK:
                    stack.add(new Mark());
                    return;
                case BININT:
                    stack.add(Long.valueOf(readInt32()));
                    return;
                case BININT1:
                    stack.add(Long.valueOf(readByte()));
                    return;
                case BININT2:
                    stack.add(Long.valueOf(readUInt16()));
                    return;
                case LONG1:
                    stack.add(Long.valueOf(readLongBytes(readByte())));
                    return;
                case LONG4:
                    stack.add(Long.valueOf(readLongBytes(readInt32())));
                    return;
                case BINFLOAT:
                    stack.add(Double.valueOf(readBinFloat()));
                    return;
                case SHORT_BINSTRING:
                    stack.add(readBytes(readByte()));
                    return;
                case BINSTRING:
                    stack.add(readBytes(readInt32()));
                    return;
                case BINUNICODE:
                    stack.add(readUtf8(readInt32()));
                    return;
                case BINPUT:
                    memo.put(Integer.valueOf(readByte()), peek());
                    return;
                case LONG_BINPUT:
                    memo.put(Integer.valueOf(readInt32()), peek());
                    return;
                case BINGET:
                    stack.add(memoGet(readByte()));
                    return;
                case LONG_BINGET:
                    stack.add(memoGet(readInt32()));
                    return;
                case APPEND:
                    appendOne();
                    return;
                case APPENDS:
                    appendMany();
                    return;
                case SETITEM:
                    setOne();
                    return;
                case SETITEMS:
                    setMany();
                    return;
                case TUPLE:
                    stack.add(popMark());
                    return;
                case TUPLE1:
                    stack.add(tuple(1));
                    return;
                case TUPLE2:
                    stack.add(tuple(2));
                    return;
                case TUPLE3:
                    stack.add(tuple(3));
                    return;
                case BUILD:
                    pop();
                    return;
                default:
                    throw new IOException("неизвестный pickle opcode " + op);
            }
        }

        private Object peek() throws IOException {
            if (stack.isEmpty()) {
                throw new IOException("пустой стек pickle");
            }
            return stack.get(stack.size() - 1);
        }

        private Object pop() throws IOException {
            if (stack.isEmpty()) {
                throw new IOException("пустой стек pickle");
            }
            return stack.remove(stack.size() - 1);
        }

        private void appendOne() throws IOException {
            Object value = pop();
            Object list = peek();
            asList(list).add(value);
        }

        private void appendMany() throws IOException {
            List<Object> items = popMark();
            Object list = peek();
            asList(list).addAll(items);
        }

        @SuppressWarnings("unchecked")
        private void setOne() throws IOException {
            Object value = pop();
            Object key = pop();
            Object dict = peek();
            asMap(dict).put(key, value);
        }

        @SuppressWarnings("unchecked")
        private void setMany() throws IOException {
            List<Object> items = popMark();
            Object dict = peek();
            Map<Object, Object> map = asMap(dict);
            if ((items.size() & 1) != 0) {
                throw new IOException("нечётный SETITEMS");
            }
            for (int i = 0; i < items.size(); i += 2) {
                map.put(items.get(i), items.get(i + 1));
            }
        }

        private List<Object> tuple(int n) throws IOException {
            if (stack.size() < n) {
                throw new IOException("короткий кортеж");
            }
            List<Object> out = new ArrayList<Object>(n);
            int from = stack.size() - n;
            for (int i = from; i < stack.size(); i++) {
                out.add(stack.get(i));
            }
            for (int i = 0; i < n; i++) {
                stack.remove(stack.size() - 1);
            }
            return out;
        }

        private List<Object> popMark() throws IOException {
            int mark = -1;
            for (int i = stack.size() - 1; i >= 0; i--) {
                if (stack.get(i) instanceof Mark) {
                    mark = i;
                    break;
                }
            }
            if (mark < 0) {
                throw new IOException("нет MARK");
            }
            List<Object> items = new ArrayList<Object>();
            for (int i = mark + 1; i < stack.size(); i++) {
                items.add(stack.get(i));
            }
            while (stack.size() > mark) {
                stack.remove(stack.size() - 1);
            }
            return items;
        }

        @SuppressWarnings("unchecked")
        private List<Object> asList(Object value) throws IOException {
            if (value instanceof List) {
                return (List<Object>) value;
            }
            throw new IOException("ожидался список");
        }

        @SuppressWarnings("unchecked")
        private Map<Object, Object> asMap(Object value) throws IOException {
            if (value instanceof Map) {
                return (Map<Object, Object>) value;
            }
            throw new IOException("ожидался словарь");
        }

        private Object memoGet(int key) throws IOException {
            Object value = memo.get(Integer.valueOf(key));
            if (value == null && !memo.containsKey(Integer.valueOf(key))) {
                throw new IOException("нет memo " + key);
            }
            return value;
        }

        private int readByte() throws IOException {
            if (pos >= data.length) {
                throw new IOException("обрыв pickle");
            }
            return data[pos++] & 0xff;
        }

        private int readUInt16() throws IOException {
            int a = readByte();
            int b = readByte();
            return a | (b << 8);
        }

        private int readInt32() throws IOException {
            int a = readByte();
            int b = readByte();
            int c = readByte();
            int d = readByte();
            return a | (b << 8) | (c << 16) | (d << 24);
        }

        private long readLongBytes(int n) throws IOException {
            if (n < 0 || n > 8) {
                throw new IOException("LONG слишком длинный");
            }
            long value = 0;
            for (int i = 0; i < n; i++) {
                value |= ((long) readByte()) << (8 * i);
            }
            if (n > 0) {
                int last = data[pos - 1];
                if (last < 0 && n < 8) {
                    value |= -1L << (8 * n);
                }
            }
            return value;
        }

        private double readBinFloat() throws IOException {
            long bits = 0;
            for (int i = 0; i < 8; i++) {
                bits = (bits << 8) | readByte();
            }
            return Double.longBitsToDouble(bits);
        }

        private byte[] readBytes(int n) throws IOException {
            if (n < 0 || pos + n > data.length) {
                throw new IOException("обрыв строки pickle");
            }
            byte[] out = new byte[n];
            System.arraycopy(data, pos, out, 0, n);
            pos += n;
            return out;
        }

        private String readUtf8(int n) throws IOException {
            return new String(readBytes(n), "UTF-8");
        }
    }

    private static final class Mark {
    }
}
