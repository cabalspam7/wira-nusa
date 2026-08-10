/**
 * Satu entitas di layar: pemain lain, karakter kita, atau mob.
 *
 * Posisi hasil server disimpan di tujuanX; posisi gambar (x) dikejar
 * pelan-pelan supaya gerakan halus walau paket datang 10 kali sedetik.
 * Semua bilangan bulat -- CLDC 1.0 tidak punya float.
 */
public final class Ent {

    public static final int JENIS_PEMAIN = 0;
    public static final int JENIS_MOB = 1;

    public static final int ANIM_IDLE = 0;
    public static final int ANIM_JALAN = 1;
    public static final int ANIM_SERANG = 2;
    public static final int ANIM_KENA = 3;
    public static final int ANIM_MATI = 4;

    public int jenis;
    public int eid;
    public String nama;
    public int job;        // untuk mob: id mob
    public int rambut;
    public int kulit;
    public int level;
    public int x;
    public int tujuanX;
    public int y;
    public int arah = 1;
    public int hp;
    public int hpMaks = 1;
    public boolean hidup = true;

    // perlengkapan yang terlihat (paperdoll)
    public int senjata;
    public int plus;
    public int baju;
    public int topi;
    public int sayap;

    // animasi
    public int anim = ANIM_IDLE;
    public int frame;
    public int tickAnim;
    public int timerAnim;

    // angka damage melayang
    public int dmgTeks;
    public int dmgTimer;
    public int dmgY;

    public Ent(int jenis, int eid) {
        this.jenis = jenis;
        this.eid = eid;
    }

    public void setAnim(int a) {
        if (anim == a) {
            return;
        }
        anim = a;
        frame = 0;
        tickAnim = 0;
        timerAnim = (a == ANIM_SERANG) ? 6 : (a == ANIM_KENA ? 3 : 0);
    }

    public void tampilkanDamage(int nilai) {
        dmgTeks = nilai;
        dmgTimer = 18;
        dmgY = 0;
        if (hidup) {
            setAnim(ANIM_KENA);
        }
    }

    /** Dipanggil sekali tiap frame game. */
    public void perbarui() {
        int beda = tujuanX - x;
        if (beda != 0) {
            int langkah = beda / 3;
            if (langkah == 0) {
                langkah = beda > 0 ? 1 : -1;
            }
            if (langkah > 12) {
                langkah = 12;
            }
            if (langkah < -12) {
                langkah = -12;
            }
            x += langkah;
            if (hidup && anim != ANIM_SERANG && anim != ANIM_MATI) {
                setAnim(ANIM_JALAN);
            }
        } else if (hidup && anim == ANIM_JALAN) {
            setAnim(ANIM_IDLE);
        }

        if (timerAnim > 0) {
            timerAnim--;
            if (timerAnim == 0 && anim != ANIM_MATI) {
                setAnim(ANIM_IDLE);
            }
        }

        tickAnim++;
        int jeda = (anim == ANIM_SERANG) ? 2 : 4;
        if (tickAnim >= jeda) {
            tickAnim = 0;
            frame++;
            int jumlah = Res.jumlahFrame(anim);
            if (frame >= jumlah) {
                frame = (anim == ANIM_MATI) ? jumlah - 1 : 0;
            }
        }

        if (dmgTimer > 0) {
            dmgTimer--;
            dmgY -= 1;
        }
    }

    public void mati() {
        hidup = false;
        hp = 0;
        setAnim(ANIM_MATI);
        timerAnim = 0;
    }

    public void hidupLagi(int hpBaru, int hpMaksBaru) {
        hidup = true;
        hp = hpBaru;
        hpMaks = hpMaksBaru;
        setAnim(ANIM_IDLE);
    }

    /** Lebar bar hp di atas kepala, dalam piksel dari lebar penuh. */
    public int barHp(int lebarPenuh) {
        if (hpMaks <= 0) {
            return 0;
        }
        int w = hp * lebarPenuh / hpMaks;
        if (w < 0) {
            w = 0;
        }
        if (w > lebarPenuh) {
            w = lebarPenuh;
        }
        return w;
    }
}
