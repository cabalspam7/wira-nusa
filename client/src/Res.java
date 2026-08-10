import java.util.Hashtable;
import javax.microedition.lcdui.Graphics;
import javax.microedition.lcdui.Image;
import javax.microedition.lcdui.game.Sprite;

/**
 * Gudang gambar + penggambar paperdoll.
 *
 * Semua lembar animasi punya 12 frame 24x32 berderet horizontal dengan
 * urutan: idle(2) jalan(4) serang(3) kena(1) mati(2). Karena semua
 * lapisan memakai urutan yang sama, tinggal menumpuk lembar kaki, badan,
 * kepala, rambut, topi, sayap, dan senjata pada frame yang sama.
 *
 * Gambar dimuat malas (lazy) dan disimpan di Hashtable supaya HP lama
 * tidak kehabisan heap saat masuk map.
 */
public final class Res {

    public static final int CELL_W = 24;
    public static final int CELL_H = 32;

    private static final int[] AWAL_FRAME = {0, 2, 6, 9, 10};
    private static final int[] JUMLAH_FRAME = {2, 4, 3, 1, 2};

    private static final Hashtable cache = new Hashtable();
    private static final String[] NAMA_MOB = {
        "", "celeng", "kunti", "genderuwo", "buto", "naga"
    };

    private Res() {
    }

    public static int jumlahFrame(int anim) {
        if (anim < 0 || anim >= JUMLAH_FRAME.length) {
            return 1;
        }
        return JUMLAH_FRAME[anim];
    }

    public static int indeksFrame(int anim, int frame) {
        if (anim < 0 || anim >= AWAL_FRAME.length) {
            return 0;
        }
        int n = JUMLAH_FRAME[anim];
        if (frame >= n) {
            frame = n - 1;
        }
        if (frame < 0) {
            frame = 0;
        }
        return AWAL_FRAME[anim] + frame;
    }

    /** Muat gambar sekali, lalu pakai dari cache. Null kalau tidak ada. */
    public static Image gambar(String path) {
        Object ada = cache.get(path);
        if (ada != null) {
            return (Image) ada;
        }
        try {
            Image img = Image.createImage(path);
            cache.put(path, img);
            return img;
        } catch (Exception e) {
            return null;
        }
    }

    public static void bersihkan() {
        cache.clear();
        System.gc();
    }

    private static void lapis(Graphics g, String path, int kolom, int x, int y,
            boolean cermin) {
        Image img = gambar(path);
        if (img == null) {
            return;
        }
        int sx = kolom * CELL_W;
        if (sx + CELL_W > img.getWidth()) {
            sx = 0;
        }
        int transform = cermin ? Sprite.TRANS_MIRROR : Sprite.TRANS_NONE;
        g.drawRegion(img, sx, 0, CELL_W, CELL_H, transform, x, y,
                Graphics.LEFT | Graphics.TOP);
    }

    /**
     * Gambar satu karakter lengkap. x,y adalah titik kaki (tengah bawah).
     */
    public static void karakter(Graphics g, Ent e, int x, int y) {
        int kolom = indeksFrame(e.anim, e.frame);
        boolean cermin = e.arah < 0;
        int gx = x - CELL_W / 2;
        int gy = y - CELL_H;
        int job = e.job & 3;

        if (e.sayap > 0) {
            lapis(g, "/c/wing/s" + (e.sayap % 3) + ".png", kolom, gx, gy, cermin);
        }
        lapis(g, "/c/leg/k" + job + ".png", kolom, gx, gy, cermin);
        lapis(g, "/c/body/b" + job + ".png", kolom, gx, gy, cermin);
        lapis(g, "/c/head/h" + (e.kulit & 3) + ".png", kolom, gx, gy, cermin);
        if (e.topi > 0) {
            lapis(g, "/c/hat/t" + (e.topi % 3) + "_" + (e.kulit & 3) + ".png",
                    kolom, gx, gy, cermin);
        } else {
            lapis(g, "/c/hair/r" + (e.rambut & 3) + "_" + (e.kulit & 3) + ".png",
                    kolom, gx, gy, cermin);
        }
        if (e.senjata > 0) {
            int tingkat = (e.senjata % 10);
            if (tingkat > 2) {
                tingkat = 2;
            }
            lapis(g, "/weapon/" + Item.namaJob(job).toLowerCase() + "/w"
                    + tingkat + ".png", kolom, gx, gy, cermin);
        }
        if (e.plus >= 7) {
            // senjata +7 ke atas berkilau: bingkai tipis kuning
            g.setColor(0xFFD54A);
            g.drawRect(gx + 2, gy + 2, CELL_W - 5, CELL_H - 5);
        }
    }

    /** Gambar mob. Lembar mob punya 6 frame dengan ukurannya sendiri. */
    public static void mob(Graphics g, Ent e, int x, int y) {
        int id = e.job;
        if (id < 1 || id >= NAMA_MOB.length) {
            id = 1;
        }
        Image img = gambar("/mob/" + NAMA_MOB[id] + ".png");
        if (img == null) {
            g.setColor(0x884422);
            g.fillRect(x - 8, y - 16, 16, 16);
            return;
        }
        int lebar = img.getWidth() / 6;
        int tinggi = img.getHeight();
        int frame = e.frame % 6;
        if (e.anim == Ent.ANIM_MATI) {
            frame = 5;
        }
        int transform = e.arah < 0 ? Sprite.TRANS_MIRROR : Sprite.TRANS_NONE;
        g.drawRegion(img, frame * lebar, 0, lebar, tinggi, transform,
                x - lebar / 2, y - tinggi, Graphics.LEFT | Graphics.TOP);
    }

    /** Latar berlapis: makin jauh makin pelan (parallax). */
    public static void latar(Graphics g, String tema, int kameraX, int lebarLayar,
            int tinggiLayar) {
        for (int lapisan = 0; lapisan < 3; lapisan++) {
            Image img = gambar("/bg/" + tema + "_" + lapisan + ".png");
            if (img == null) {
                continue;
            }
            int bagi = 8 - lapisan * 3;      // 8, 5, 2
            if (bagi < 1) {
                bagi = 1;
            }
            int geser = (kameraX / bagi) % img.getWidth();
            if (geser < 0) {
                geser += img.getWidth();
            }
            int y = tinggiLayar - img.getHeight();
            if (lapisan == 0) {
                y = 0;
            }
            int x = -geser;
            while (x < lebarLayar) {
                g.drawImage(img, x, y, Graphics.LEFT | Graphics.TOP);
                x += img.getWidth();
            }
        }
    }

    /** Lantai berulang dari satu ubin. */
    public static void lantai(Graphics g, String tile, int kameraX, int tanahY,
            int lebarLayar, int tinggiLayar) {
        Image img = gambar("/tile/" + tile + ".png");
        if (img == null) {
            g.setColor(0x3B2E22);
            g.fillRect(0, tanahY, lebarLayar, tinggiLayar - tanahY);
            return;
        }
        int w = img.getWidth();
        int h = img.getHeight();
        int geser = kameraX % w;
        if (geser < 0) {
            geser += w;
        }
        for (int y = tanahY; y < tinggiLayar; y += h) {
            for (int x = -geser; x < lebarLayar; x += w) {
                g.drawImage(img, x, y, Graphics.LEFT | Graphics.TOP);
            }
        }
    }
}
