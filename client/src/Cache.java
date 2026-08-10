import javax.microedition.rms.RecordStore;

/**
 * Penyimpanan kecil di HP lewat RMS: host, port, nama akun, dan
 * pengaturan (suara, tombol). Sandi TIDAK pernah disimpan.
 */
public final class Cache {

    private static final String NAMA_RS = "wiranusa";

    public static String host = "127.0.0.1";
    public static int port = 7777;
    public static String akun = "";
    public static boolean suara = true;

    private Cache() {
    }

    public static void muat() {
        RecordStore rs = null;
        try {
            rs = RecordStore.openRecordStore(NAMA_RS, true);
            if (rs.getNumRecords() < 1) {
                return;
            }
            byte[] data = rs.getRecord(1);
            if (data == null) {
                return;
            }
            String isi = new String(data, "UTF-8");
            String[] bagian = pisah(isi, '\n');
            if (bagian.length > 0 && bagian[0].length() > 0) {
                host = bagian[0];
            }
            if (bagian.length > 1) {
                try {
                    port = Integer.parseInt(bagian[1]);
                } catch (NumberFormatException e) {
                }
            }
            if (bagian.length > 2) {
                akun = bagian[2];
            }
            if (bagian.length > 3) {
                suara = "1".equals(bagian[3]);
            }
        } catch (Exception e) {
        } finally {
            tutup(rs);
        }
    }

    public static void simpan() {
        RecordStore rs = null;
        try {
            rs = RecordStore.openRecordStore(NAMA_RS, true);
            String isi = host + "\n" + port + "\n" + akun + "\n"
                    + (suara ? "1" : "0");
            byte[] data = isi.getBytes("UTF-8");
            if (rs.getNumRecords() < 1) {
                rs.addRecord(data, 0, data.length);
            } else {
                rs.setRecord(1, data, 0, data.length);
            }
        } catch (Exception e) {
        } finally {
            tutup(rs);
        }
    }

    private static void tutup(RecordStore rs) {
        if (rs != null) {
            try {
                rs.closeRecordStore();
            } catch (Exception e) {
            }
        }
    }

    /** CLDC 1.0 tidak punya String.split. */
    public static String[] pisah(String teks, char pemisah) {
        int jumlah = 1;
        for (int i = 0; i < teks.length(); i++) {
            if (teks.charAt(i) == pemisah) {
                jumlah++;
            }
        }
        String[] hasil = new String[jumlah];
        int mulai = 0;
        int n = 0;
        for (int i = 0; i < teks.length(); i++) {
            if (teks.charAt(i) == pemisah) {
                hasil[n++] = teks.substring(mulai, i);
                mulai = i + 1;
            }
        }
        hasil[n] = teks.substring(mulai);
        return hasil;
    }
}
