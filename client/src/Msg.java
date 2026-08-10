import java.io.ByteArrayOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;

/**
 * Opcode dan pembaca/penulis paket. Format sama persis dengan
 * server/protocol.py: [u16 panjang][u8 opcode][payload].
 *
 * Ditulis untuk CLDC 1.0: tidak ada generics, tidak ada float,
 * tidak ada StringBuilder.
 */
public final class Msg {

    // ---- klien ke server
    public static final int C_LOGIN = 1;
    public static final int C_DAFTAR = 2;
    public static final int C_BUAT_CHAR = 3;
    public static final int C_PILIH_CHAR = 4;
    public static final int C_GERAK = 10;
    public static final int C_SERANG = 11;
    public static final int C_AMBIL = 12;
    public static final int C_CHAT = 13;
    public static final int C_PAKAI_ITEM = 14;
    public static final int C_PAKAI_EQUIP = 15;
    public static final int C_LEPAS_EQUIP = 16;
    public static final int C_PINDAH_MAP = 17;
    public static final int C_PARTY = 18;
    public static final int C_TRADE = 19;
    public static final int C_NAIK_SKILL = 20;
    public static final int C_TOKO = 21;
    public static final int C_UPGRADE = 22;
    public static final int C_QUEST = 23;
    public static final int C_GUILD = 24;
    public static final int C_MAIL = 25;
    public static final int C_LELANG = 26;
    public static final int C_PING = 30;

    // ---- server ke klien
    public static final int S_LOGIN_OK = 100;
    public static final int S_TOLAK = 101;
    public static final int S_DAFTAR_CHAR = 102;
    public static final int S_MASUK_MAP = 103;
    public static final int S_ENTITAS_TAMBAH = 104;
    public static final int S_ENTITAS_HAPUS = 105;
    public static final int S_ENTITAS_GERAK = 106;
    public static final int S_ENTITAS_SERANG = 107;
    public static final int S_DAMAGE = 108;
    public static final int S_MATI = 109;
    public static final int S_HIDUP_LAGI = 110;
    public static final int S_DROP_TAMBAH = 111;
    public static final int S_DROP_HAPUS = 112;
    public static final int S_INVENTORI = 113;
    public static final int S_STATUS = 114;
    public static final int S_CHAT = 115;
    public static final int S_PARTY = 116;
    public static final int S_TRADE = 117;
    public static final int S_NAIK_LEVEL = 118;
    public static final int S_TOKO_ISI = 119;
    public static final int S_PESAN = 120;
    public static final int S_QUEST = 121;
    public static final int S_GUILD = 122;
    public static final int S_MAIL = 123;
    public static final int S_LELANG = 124;
    public static final int S_PONG = 130;

    private Msg() {
    }

    /** Penulis paket. Dipakai berantai: new Msg.Tulis(op).b(1).teks("x") */
    public static final class Tulis {
        private final ByteArrayOutputStream buf;
        private final DataOutputStream out;
        private final int opcode;

        public Tulis(int opcode) {
            this.opcode = opcode;
            this.buf = new ByteArrayOutputStream(32);
            this.out = new DataOutputStream(buf);
        }

        public Tulis b(int v) {
            try {
                out.writeByte(v & 0xFF);
            } catch (IOException e) {
            }
            return this;
        }

        public Tulis sb(int v) {
            try {
                out.writeByte(v);
            } catch (IOException e) {
            }
            return this;
        }

        public Tulis s(int v) {
            try {
                out.writeShort(v);
            } catch (IOException e) {
            }
            return this;
        }

        public Tulis us(int v) {
            try {
                out.writeShort(v & 0xFFFF);
            } catch (IOException e) {
            }
            return this;
        }

        public Tulis i(int v) {
            try {
                out.writeInt(v);
            } catch (IOException e) {
            }
            return this;
        }

        public Tulis teks(String v) {
            try {
                out.writeUTF(v == null ? "" : v);
            } catch (IOException e) {
            }
            return this;
        }

        /** Susun jadi paket lengkap dengan header panjang. */
        public byte[] paket() {
            byte[] isi = buf.toByteArray();
            int panjang = isi.length + 1;
            byte[] paket = new byte[panjang + 2];
            paket[0] = (byte) ((panjang >> 8) & 0xFF);
            paket[1] = (byte) (panjang & 0xFF);
            paket[2] = (byte) (opcode & 0xFF);
            System.arraycopy(isi, 0, paket, 3, isi.length);
            return paket;
        }
    }

    /** Pembaca payload paket yang sudah utuh. */
    public static final class Baca {
        private final byte[] data;
        private int pos;
        public final int opcode;

        public Baca(int opcode, byte[] data) {
            this.opcode = opcode;
            this.data = data;
            this.pos = 0;
        }

        public int sisa() {
            return data.length - pos;
        }

        public int b() {
            if (pos >= data.length) {
                return 0;
            }
            return data[pos++] & 0xFF;
        }

        public int sb() {
            if (pos >= data.length) {
                return 0;
            }
            return data[pos++];
        }

        public int s() {
            int v = (short) (((b() & 0xFF) << 8) | (b() & 0xFF));
            return v;
        }

        public int us() {
            return ((b() & 0xFF) << 8) | (b() & 0xFF);
        }

        public int i() {
            return (b() << 24) | (b() << 16) | (b() << 8) | b();
        }

        /** Modified UTF-8 sama seperti DataInputStream.readUTF. */
        public String teks() {
            int panjang = us();
            if (panjang <= 0 || panjang > sisa()) {
                pos = data.length;
                return "";
            }
            char[] keluar = new char[panjang];
            int n = 0;
            int akhir = pos + panjang;
            while (pos < akhir) {
                int c = data[pos] & 0xFF;
                if (c < 0x80) {
                    pos++;
                    keluar[n++] = (char) c;
                } else if ((c & 0xE0) == 0xC0) {
                    int c2 = data[pos + 1] & 0x3F;
                    pos += 2;
                    keluar[n++] = (char) (((c & 0x1F) << 6) | c2);
                } else {
                    int c2 = data[pos + 1] & 0x3F;
                    int c3 = data[pos + 2] & 0x3F;
                    pos += 3;
                    keluar[n++] = (char) (((c & 0x0F) << 12) | (c2 << 6) | c3);
                }
            }
            return new String(keluar, 0, n);
        }
    }
}
