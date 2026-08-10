/**
 * Tabel item sisi klien: cuma untuk MENAMPILKAN nama, jenis, dan ikon.
 * Semua angka yang berpengaruh ke permainan (atk, dfn, harga akhir)
 * tetap dihitung server -- klien tidak boleh dipercaya.
 */
public final class Item {

    public static final int JENIS_MINUM = 0;
    public static final int JENIS_SENJATA = 1;
    public static final int JENIS_BAJU = 2;
    public static final int JENIS_TOPI = 3;
    public static final int JENIS_SAYAP = 4;
    public static final int JENIS_BAHAN = 5;

    /** id, jenis, nama */
    private static final int[] ID = {
        100, 101, 102,
        200, 201, 202,
        210, 211, 212,
        220, 221, 222,
        230, 231, 232,
        300, 301, 302,
        400, 401, 402,
        500, 501, 502,
        600, 601, 602, 603
    };

    private static final int[] JENIS = {
        0, 0, 0,
        1, 1, 1,
        1, 1, 1,
        1, 1, 1,
        1, 1, 1,
        2, 2, 2,
        3, 3, 3,
        4, 4, 4,
        5, 5, 5, 5
    };

    private static final String[] NAMA = {
        "Ramuan Merah", "Ramuan Biru", "Batu Pulang",
        "Pedang Kayu", "Pedang Baja", "Pedang Kawah",
        "Sepasang Belati", "Sepasang Baja", "Sepasang Naga",
        "Tongkat Bambu", "Tongkat Ukir", "Tongkat Lebur",
        "Senapan Sumpit", "Senapan Laras", "Senapan Kawah",
        "Baju Kain", "Baju Kulit", "Baju Zirah",
        "Ikat Kepala", "Topi Anyam", "Mahkota Gurat",
        "Selendang", "Sayap Kunang", "Sayap Naga",
        "Batu Tempa", "Taring Celeng", "Rambut Kunti", "Sisik Naga"
    };

    private Item() {
    }

    private static int indeks(int id) {
        for (int i = 0; i < ID.length; i++) {
            if (ID[i] == id) {
                return i;
            }
        }
        return -1;
    }

    public static String nama(int id) {
        int i = indeks(id);
        return i < 0 ? ("Item " + id) : NAMA[i];
    }

    public static int jenis(int id) {
        int i = indeks(id);
        return i < 0 ? JENIS_BAHAN : JENIS[i];
    }

    public static boolean bisaDipakai(int id) {
        int j = jenis(id);
        return j >= JENIS_SENJATA && j <= JENIS_SAYAP;
    }

    public static boolean bisaDiminum(int id) {
        return jenis(id) == JENIS_MINUM;
    }

    /** Nama lengkap dengan tanda upgrade, misal "Pedang Baja +7". */
    public static String namaPlus(int id, int plus) {
        if (plus <= 0) {
            return nama(id);
        }
        return nama(id) + " +" + plus;
    }

    public static String namaSlotEquip(int slot) {
        if (slot == 0) {
            return "Senjata";
        }
        if (slot == 1) {
            return "Baju";
        }
        if (slot == 2) {
            return "Topi";
        }
        return "Sayap";
    }

    public static String namaJob(int job) {
        if (job == 0) {
            return "Pedang";
        }
        if (job == 1) {
            return "Sepasang";
        }
        if (job == 2) {
            return "Dukun";
        }
        return "Senapan";
    }
}
