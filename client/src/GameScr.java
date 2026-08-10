import java.util.Hashtable;
import java.util.Vector;
import javax.microedition.lcdui.Canvas;
import javax.microedition.lcdui.Font;
import javax.microedition.lcdui.Graphics;

/**
 * Layar dunia WIRA NUSA: menggambar map, entitas, HUD, dan semua panel
 * (tas, toko, party, skill, quest, dagang).
 *
 * Ditulis untuk CLDC 1.0 / MIDP 2.0: tanpa generics, tanpa float,
 * tanpa StringBuilder, tanpa foreach.
 */
public final class GameScr extends Canvas implements Runnable {

    // panel yang sedang terbuka
    public static final int P_TIDAK = 0;
    public static final int P_TAS = 1;
    public static final int P_TOKO = 2;
    public static final int P_PARTY = 3;
    public static final int P_SKILL = 4;
    public static final int P_QUEST = 5;
    public static final int P_TRADE = 6;
    public static final int P_GUILD = 7;
    public static final int P_MAIL = 8;
    public static final int P_LELANG = 9;
    public static final int P_SOSIAL = 10;

    private final Main app;
    private final Net net;
    private Thread loop;
    private boolean jalan;

    // ---------------------------------------------------------- dunia
    private int mapId;
    private String mapNama = "";
    private String tema = "desa";
    private String tile = "tanah";
    private int lebarMap = 1600;
    private int tanahY = 200;
    private int aman;
    private int myEid = -1;
    private int kameraX;

    private final Hashtable ents = new Hashtable();
    private Ent aku;

    private int[] portalX = new int[0];
    private int[] portalTujuan = new int[0];

    private int[] npcX = new int[0];
    private String[] npcNama = new String[0];
    private int[] npcJenis = new int[0];

    private final Vector dropId = new Vector();
    private final Vector dropInfo = new Vector();   // int[]{item, jumlah, plus, x}

    // ---------------------------------------------------------- status
    private int hp = 1;
    private int hpMaks = 1;
    private int mp;
    private int mpMaks = 1;
    private int level = 1;
    private int exp;
    private int expButuh = 1;
    private int gold;
    private int atk;
    private int dfn;
    private int poin;
    private int[] skillId = new int[0];
    private int[] skillLv = new int[0];

    // ---------------------------------------------------------- barang
    private int nInv;
    private final int[] invSlot = new int[40];
    private final int[] invId = new int[40];
    private final int[] invJumlah = new int[40];
    private final int[] invPlus = new int[40];

    private int nEq;
    private final int[] eqSlot = new int[8];
    private final int[] eqId = new int[8];
    private final int[] eqPlus = new int[8];

    // ---------------------------------------------------------- toko
    private int nToko;
    private final int[] tokoId = new int[40];
    private final int[] tokoHarga = new int[40];

    // ---------------------------------------------------------- party
    private int partyId;
    private int nParty;
    private final String[] partyNama = new String[8];
    private final int[] partyHp = new int[8];
    private final int[] partyHpMaks = new int[8];
    private final int[] partyCid = new int[8];

    // ---------------------------------------------------------- quest
    private int questMode;              // 0 dialog NPC, 1 jurnal
    private int nQuest;
    private final int[] questId = new int[16];
    private final int[] questKode = new int[16];
    private final int[] questProgres = new int[16];
    private final int[] questButuh = new int[16];
    private final int[] questJenis = new int[16];
    private final String[] questNama = new String[16];
    private final String[] questTeks = new String[16];

    // ---------------------------------------------------------- dagang
    private boolean tradeAktif;
    private String tradeLawan = "";
    private int ajakanEid = -1;
    private String ajakanNama = "";
    private int ajakanTimer;

    private int goldKamu;
    private int goldLawan;
    private boolean kunciKamu;
    private boolean kunciLawan;
    private int nTawarKamu;
    private final int[] tawarKamuId = new int[8];
    private final int[] tawarKamuJumlah = new int[8];
    private final int[] tawarKamuPlus = new int[8];
    private int nTawarLawan;
    private final int[] tawarLawanId = new int[8];
    private final int[] tawarLawanJumlah = new int[8];
    private final int[] tawarLawanPlus = new int[8];

    // tawaran yang sedang disusun di sisi klien
    private int rencanaGold;
    private int nRencana;
    private final int[] rencanaSlot = new int[8];
    private final int[] rencanaJumlah = new int[8];

    // ---------------------------------------------------------- antarmuka
    private int panel = P_TIDAK;

    // ---- guild
    private boolean punyaGuild = false;
    private int guildId;
    private String guildNama = "";
    private int guildLevel;
    private int guildExp;
    private int guildExpNaik;
    private int guildKas;
    private int guildPangkatKamu;
    private int guildMenang;
    private int guildKalah;
    private int guildBonusExp;
    private int guildBonusGold;
    private int nAnggota = 0;
    private final int[] anggotaId = new int[40];
    private final String[] anggotaNama = new String[40];
    private final int[] anggotaPangkat = new int[40];
    private final int[] anggotaSumbang = new int[40];
    private final boolean[] anggotaOnline = new boolean[40];
    private final int[] anggotaLevel = new int[40];
    private int undanganGid = -1;
    private String undanganGuild = "";
    private int warId = 0;
    private String warNamaA = "";
    private String warNamaB = "";
    private int warSkorA;
    private int warSkorB;
    private int warSisa;
    private int warTaruhan;
    private String tantanganDari = "";
    private int tantanganTaruhan = 0;

    // ---- surat
    private int nMail = 0;
    private final int[] mailId = new int[30];
    private final String[] mailDari = new String[30];
    private final String[] mailJudul = new String[30];
    private final boolean[] mailDibaca = new boolean[30];
    private final int[] mailGold = new int[30];
    private final int[] mailLampiran = new int[30];
    private int bacaId = 0;
    private String bacaDari = "";
    private String bacaJudul = "";
    private String bacaIsi = "";
    private int bacaGold = 0;
    private int bacaLampiran = 0;

    // ---- lelang
    private int lelangMode = 0;      // 0 papan umum, 1 lapak saya
    private int lelangHalaman = 0;
    private int nLelang = 0;
    private final int[] lelangId = new int[12];
    private final String[] lelangPenjual = new String[12];
    private final int[] lelangItem = new int[12];
    private final int[] lelangJumlah = new int[12];
    private final int[] lelangPlus = new int[12];
    private final int[] lelangHarga = new int[12];
    private final int[] lelangSisa = new int[12];
    private int pilih;
    private final Vector chat = new Vector();
    private String pesanBawah = "";
    private int pesanTimer;
    private int tekanKiri;
    private int tekanKanan;
    private int langkahX;
    private int kirimGerakTimer;

    public GameScr(Main app, Net net) {
        this.app = app;
        this.net = net;
        setFullScreenMode(true);
    }

    // ------------------------------------------------------------- hidup
    public void mulai() {
        if (loop != null && jalan) {
            return;
        }
        jalan = true;
        loop = new Thread(this);
        loop.start();
    }

    public void berhenti() {
        jalan = false;
        loop = null;
    }

    public void kirimChat(String teks) {
        if (teks == null) {
            return;
        }
        teks = teks.trim();
        if (teks.length() == 0) {
            return;
        }
        net.kirim(new Msg.Tulis(Msg.C_CHAT).b(0).teks(teks));
    }

    public void run() {
        int detak = 0;
        while (jalan) {
            long t0 = System.currentTimeMillis();

            Msg.Baca r = net.ambil();
            while (r != null) {
                tangani(r);
                r = net.ambil();
            }
            perbarui();
            detak++;
            if (detak % 100 == 0) {
                net.kirim(new Msg.Tulis(Msg.C_PING).i(detak));
            }
            repaint();
            serviceRepaints();
            long sisa = 100 - (System.currentTimeMillis() - t0);
            if (sisa > 0) {
                try {
                    Thread.sleep(sisa);
                } catch (InterruptedException e) {
                }
            }
        }
    }

    private void catat(String teks) {
        chat.addElement(teks);
        while (chat.size() > 5) {
            chat.removeElementAt(0);
        }
    }

    private void info(String teks) {
        pesanBawah = teks;
        pesanTimer = 30;
    }

    // ------------------------------------------------------------ paket
    private void tangani(Msg.Baca r) {
        int op = r.opcode;
        if (op == Msg.S_MASUK_MAP) {
            masukMap(r);
        } else if (op == Msg.S_ENTITAS_TAMBAH) {
            entitasTambah(r);
        } else if (op == Msg.S_ENTITAS_HAPUS) {
            ents.remove(new Integer(r.i()));
        } else if (op == Msg.S_ENTITAS_GERAK) {
            Ent e = cari(r.i());
            int x = r.s();
            int arah = r.sb();
            int state = r.b();
            if (e != null) {
                e.tujuanX = x;
                e.arah = arah == 0 ? e.arah : arah;
                if (state == 0) {
                    e.x = x;
                }
            }
        } else if (op == Msg.S_ENTITAS_SERANG) {
            Ent e = cari(r.i());
            r.us();
            r.i();
            if (e != null) {
                e.setAnim(Ent.ANIM_SERANG);
            }
        } else if (op == Msg.S_DAMAGE) {
            Ent e = cari(r.i());
            int dmg = r.i();
            int sisa = r.i();
            r.i();
            if (e != null) {
                e.hp = sisa;
                e.tampilkanDamage(dmg);
            }
        } else if (op == Msg.S_MATI) {
            Ent e = cari(r.i());
            if (e != null) {
                e.mati();
            }
        } else if (op == Msg.S_HIDUP_LAGI) {
            Ent e = cari(r.i());
            int h = r.i();
            int hm = r.i();
            if (e != null) {
                e.hidupLagi(h, hm);
            }
        } else if (op == Msg.S_DROP_TAMBAH) {
            int did = r.i();
            int[] d = new int[] {r.us(), r.us(), r.b(), r.s()};
            hapusDrop(did);
            dropId.addElement(new Integer(did));
            dropInfo.addElement(d);
        } else if (op == Msg.S_DROP_HAPUS) {
            hapusDrop(r.i());
        } else if (op == Msg.S_INVENTORI) {
            bacaInventori(r);
        } else if (op == Msg.S_STATUS) {
            bacaStatus(r);
        } else if (op == Msg.S_CHAT) {
            int kanal = r.b();
            String nama = r.teks();
            String teks = r.teks();
            catat((kanal == 1 ? "[party] " : (kanal == 2 ? "[umum] " : ""))
                    + nama + ": " + teks);
        } else if (op == Msg.S_PARTY) {
            bacaParty(r);
        } else if (op == Msg.S_TRADE) {
            bacaTrade(r);
        } else if (op == Msg.S_NAIK_LEVEL) {
            Ent e = cari(r.i());
            int lv = r.s();
            if (e != null) {
                e.level = lv;
            }
            if (e != null && e == aku) {
                catat("Naik ke level " + lv + "!");
            }
        } else if (op == Msg.S_TOKO_ISI) {
            nToko = r.b();
            if (nToko > tokoId.length) {
                nToko = tokoId.length;
            }
            for (int i = 0; i < nToko; i++) {
                tokoId[i] = r.us();
                tokoHarga[i] = r.i();
            }
            panel = P_TOKO;
            pilih = 0;
        } else if (op == Msg.S_QUEST) {
            bacaQuest(r);
        } else if (op == Msg.S_GUILD) {
            bacaGuild(r);
        } else if (op == Msg.S_MAIL) {
            bacaMail(r);
        } else if (op == Msg.S_LELANG) {
            bacaLelang(r);
        } else if (op == Msg.S_PESAN || op == Msg.S_TOLAK) {
            info(r.teks());
        }
    }

    private Ent cari(int eid) {
        Object o = ents.get(new Integer(eid));
        return o == null ? null : (Ent) o;
    }

    private void hapusDrop(int did) {
        for (int i = 0; i < dropId.size(); i++) {
            if (((Integer) dropId.elementAt(i)).intValue() == did) {
                dropId.removeElementAt(i);
                dropInfo.removeElementAt(i);
                return;
            }
        }
    }

    private void masukMap(Msg.Baca r) {
        ents.clear();
        dropId.removeAllElements();
        dropInfo.removeAllElements();
        mapId = r.b();
        mapNama = r.teks();
        tema = r.teks();
        tile = r.teks();
        lebarMap = r.us();
        tanahY = r.s();
        aman = r.b();
        myEid = r.i();
        int x = r.s();

        int np = r.b();
        portalX = new int[np];
        portalTujuan = new int[np];
        for (int i = 0; i < np; i++) {
            portalX[i] = r.us();
            portalTujuan[i] = r.b();
            r.us();
        }
        int nn = r.b();
        npcX = new int[nn];
        npcNama = new String[nn];
        npcJenis = new int[nn];
        for (int i = 0; i < nn; i++) {
            npcX[i] = r.us();
            npcNama[i] = r.teks();
            npcJenis[i] = r.b();
        }

        aku = new Ent(Ent.JENIS_PEMAIN, myEid);
        aku.nama = app.namaKarakter;
        aku.job = app.jobKarakter;
        aku.rambut = app.rambutKarakter;
        aku.kulit = app.kulitKarakter;
        aku.x = x;
        aku.tujuanX = x;
        aku.hp = hp;
        aku.hpMaks = hpMaks;
        ents.put(new Integer(myEid), aku);
        langkahX = x;
        panel = P_TIDAK;
        catat("Masuk " + mapNama);
        Res.bersihkan();
    }

    private void entitasTambah(Msg.Baca r) {
        int jenis = r.b();
        int eid = r.i();
        Ent e = cari(eid);
        if (e == null) {
            e = new Ent(jenis == 0 ? Ent.JENIS_PEMAIN : Ent.JENIS_MOB, eid);
            ents.put(new Integer(eid), e);
        }
        e.nama = r.teks();
        e.job = r.b();
        e.rambut = r.b();
        e.kulit = r.b();
        e.level = r.s();
        int x = r.s();
        e.y = r.s();
        e.arah = r.sb();
        e.hp = r.i();
        e.hpMaks = r.i();
        e.senjata = r.us();
        e.plus = r.b();
        e.baju = r.us();
        e.topi = r.us();
        e.sayap = r.us();
        if (e.hp > 0) {
            e.hidup = true;
        }
        e.tujuanX = x;
        if (eid == myEid) {
            aku = e;
            e.x = x;
            langkahX = x;
        } else if (e.x == 0) {
            e.x = x;
        }
    }

    private void bacaInventori(Msg.Baca r) {
        nInv = r.b();
        if (nInv > invId.length) {
            nInv = invId.length;
        }
        for (int i = 0; i < nInv; i++) {
            invSlot[i] = r.b();
            invId[i] = r.us();
            invJumlah[i] = r.us();
            invPlus[i] = r.b();
        }
        nEq = r.b();
        if (nEq > eqId.length) {
            nEq = eqId.length;
        }
        for (int i = 0; i < nEq; i++) {
            eqSlot[i] = r.b();
            eqId[i] = r.us();
            r.us();
            eqPlus[i] = r.b();
        }
        if (pilih >= nInv) {
            pilih = nInv > 0 ? nInv - 1 : 0;
        }
    }

    private void bacaStatus(Msg.Baca r) {
        hp = r.i();
        hpMaks = r.i();
        mp = r.i();
        mpMaks = r.i();
        level = r.s();
        exp = r.i();
        expButuh = r.i();
        gold = r.i();
        atk = r.s();
        dfn = r.s();
        poin = r.b();
        int n = r.b();
        skillId = new int[n];
        skillLv = new int[n];
        for (int i = 0; i < n; i++) {
            skillId[i] = r.us();
            skillLv[i] = r.b();
        }
        if (aku != null) {
            aku.hp = hp;
            aku.hpMaks = hpMaks;
            aku.level = level;
        }
    }

    private void bacaParty(Msg.Baca r) {
        partyId = r.i();
        nParty = r.b();
        if (nParty > partyNama.length) {
            nParty = partyNama.length;
        }
        for (int i = 0; i < nParty; i++) {
            partyCid[i] = r.i();
            partyNama[i] = r.teks();
            partyHp[i] = r.i();
            partyHpMaks[i] = r.i();
        }
    }

    private void bacaQuest(Msg.Baca r) {
        questMode = r.b();
        nQuest = r.b();
        if (nQuest > questId.length) {
            nQuest = questId.length;
        }
        for (int i = 0; i < nQuest; i++) {
            questId[i] = r.us();
            questKode[i] = r.b();
            questProgres[i] = r.us();
            questButuh[i] = r.us();
            questJenis[i] = r.b();
            r.us();                     // sasaran, cukup untuk server
            questNama[i] = r.teks();
            questTeks[i] = r.teks();
        }
        panel = P_QUEST;
        if (pilih >= nQuest) {
            pilih = 0;
        }
    }

    private void bacaTrade(Msg.Baca r) {
        int mode = r.b();
        if (mode == 0) {
            ajakanEid = r.i();
            ajakanNama = r.teks();
            ajakanTimer = 200;
            info(ajakanNama + " mengajak dagang - tekan 6 untuk terima");
        } else if (mode == 1) {
            r.i();
            tradeLawan = r.teks();
            tradeAktif = true;
            ajakanEid = -1;
            bersihkanRencana();
            panel = P_TRADE;
            pilih = 0;
        } else if (mode == 2) {
            goldKamu = r.i();
            nTawarKamu = r.b();
            if (nTawarKamu > tawarKamuId.length) {
                nTawarKamu = tawarKamuId.length;
            }
            for (int i = 0; i < nTawarKamu; i++) {
                tawarKamuId[i] = r.us();
                tawarKamuJumlah[i] = r.us();
                tawarKamuPlus[i] = r.b();
            }
            goldLawan = r.i();
            nTawarLawan = r.b();
            if (nTawarLawan > tawarLawanId.length) {
                nTawarLawan = tawarLawanId.length;
            }
            for (int i = 0; i < nTawarLawan; i++) {
                tawarLawanId[i] = r.us();
                tawarLawanJumlah[i] = r.us();
                tawarLawanPlus[i] = r.b();
            }
            kunciKamu = r.b() == 1;
            kunciLawan = r.b() == 1;
        } else if (mode == 3) {
            tradeAktif = false;
            panel = P_TIDAK;
            bersihkanRencana();
            catat("Dagang dengan " + tradeLawan + " berhasil");
            info("dagang berhasil");
        } else {
            tradeAktif = false;
            panel = P_TIDAK;
            bersihkanRencana();
            info("dagang batal: " + r.teks());
        }
    }

    private void bacaGuild(Msg.Baca r) {
        int mode = r.b();
        if (mode == 0) {
            punyaGuild = true;
            guildId = r.i();
            guildNama = r.teks();
            guildLevel = r.b();
            guildExp = r.i();
            guildExpNaik = r.i();
            guildKas = r.i();
            guildPangkatKamu = r.b();
            guildMenang = r.us();
            guildKalah = r.us();
            guildBonusExp = r.b();
            guildBonusGold = r.b();
            nAnggota = r.b();
            if (nAnggota > anggotaId.length) {
                nAnggota = anggotaId.length;
            }
            for (int i = 0; i < nAnggota; i++) {
                anggotaId[i] = r.i();
                anggotaNama[i] = r.teks();
                anggotaPangkat[i] = r.b();
                anggotaSumbang[i] = r.i();
                anggotaOnline[i] = r.b() == 1;
                anggotaLevel[i] = r.s();
            }
            if (panel == P_GUILD && pilih >= nAnggota) {
                pilih = 0;
            }
        } else if (mode == 1) {
            punyaGuild = false;
            nAnggota = 0;
            guildNama = "";
            guildId = 0;
        } else if (mode == 2) {
            undanganGid = r.i();
            undanganGuild = r.teks();
            String dari = r.teks();
            info(dari + " mengundangmu ke guild " + undanganGuild);
            catat("Undangan guild " + undanganGuild + " - buka menu guild, tekan 2");
        } else if (mode == 3) {
            warId = r.i();
            warNamaA = r.teks();
            warNamaB = r.teks();
            warSkorA = r.i();
            warSkorB = r.i();
            warSisa = r.i();
            warTaruhan = r.i();
        } else if (mode == 4) {
            tantanganDari = r.teks();
            tantanganTaruhan = r.i();
            info(tantanganDari + " menantang perang - taruhan " + tantanganTaruhan);
        } else if (mode == 5) {
            String pemenang = r.teks();
            int sa = r.i();
            int sb = r.i();
            int hadiah = r.i();
            boolean seri = r.b() == 1;
            warId = 0;
            if (seri) {
                catat("Perang guild berakhir seri (" + sa + " - " + sb + ")");
                info("perang guild seri");
            } else {
                catat("Perang guild dimenangkan " + pemenang + " (" + sa + " - "
                        + sb + "), kas +" + hadiah);
                info("pemenang perang: " + pemenang);
            }
        }
    }

    private void bacaMail(Msg.Baca r) {
        int mode = r.b();
        if (mode == 0) {
            nMail = r.b();
            if (nMail > mailId.length) {
                nMail = mailId.length;
            }
            for (int i = 0; i < nMail; i++) {
                mailId[i] = r.i();
                mailDari[i] = r.teks();
                mailJudul[i] = r.teks();
                mailDibaca[i] = r.b() == 1;
                mailGold[i] = r.i();
                mailLampiran[i] = r.b();
                r.i();                  // waktu kirim, belum dipakai di layar
            }
            bacaId = 0;
            if (panel == P_MAIL && pilih >= nMail) {
                pilih = 0;
            }
        } else if (mode == 1) {
            bacaId = r.i();
            bacaDari = r.teks();
            bacaJudul = r.teks();
            bacaIsi = r.teks();
            bacaGold = r.i();
            bacaLampiran = r.b();
            for (int i = 0; i < bacaLampiran; i++) {
                r.us();
                r.us();
                r.b();
            }
            panel = P_MAIL;
        }
    }

    private void bacaLelang(Msg.Baca r) {
        lelangMode = r.b();
        lelangHalaman = r.b();
        nLelang = r.b();
        if (nLelang > lelangId.length) {
            nLelang = lelangId.length;
        }
        for (int i = 0; i < nLelang; i++) {
            lelangId[i] = r.i();
            lelangPenjual[i] = r.teks();
            lelangItem[i] = r.us();
            lelangJumlah[i] = r.us();
            lelangPlus[i] = r.b();
            lelangHarga[i] = r.i();
            lelangSisa[i] = r.i();
        }
        panel = P_LELANG;
        if (pilih >= nLelang) {
            pilih = 0;
        }
    }

    private String namaPangkat(int p) {
        if (p == 2) {
            return "Ketua";
        }
        if (p == 1) {
            return "Perwira";
        }
        return "Anggota";
    }

    private void bersihkanRencana() {
        nRencana = 0;
        rencanaGold = 0;
        goldKamu = 0;
        goldLawan = 0;
        nTawarKamu = 0;
        nTawarLawan = 0;
        kunciKamu = false;
        kunciLawan = false;
    }

    // ------------------------------------------------------------ update
    private void perbarui() {
        if (tekanKiri > 0 || tekanKanan > 0) {
            int arah = tekanKanan > 0 ? 1 : -1;
            langkahX += arah * 6;
            if (langkahX < 20) {
                langkahX = 20;
            }
            if (langkahX > lebarMap - 20) {
                langkahX = lebarMap - 20;
            }
            if (aku != null) {
                aku.tujuanX = langkahX;
                aku.arah = arah;
            }
            kirimGerakTimer++;
            if (kirimGerakTimer >= 2) {
                kirimGerakTimer = 0;
                net.kirim(new Msg.Tulis(Msg.C_GERAK).s(langkahX).sb(arah).b(1));
            }
        }
        java.util.Enumeration en = ents.elements();
        while (en.hasMoreElements()) {
            ((Ent) en.nextElement()).perbarui();
        }
        if (aku != null) {
            kameraX = aku.x - getWidth() / 2;
            if (kameraX < 0) {
                kameraX = 0;
            }
            if (kameraX > lebarMap - getWidth()) {
                kameraX = lebarMap - getWidth();
            }
        }
        if (pesanTimer > 0) {
            pesanTimer--;
        }
        if (ajakanTimer > 0) {
            ajakanTimer--;
            if (ajakanTimer == 0) {
                ajakanEid = -1;
            }
        }
    }

    // ------------------------------------------------------------ gambar
    protected void paint(Graphics g) {
        int w = getWidth();
        int h = getHeight();
        g.setColor(0x101820);
        g.fillRect(0, 0, w, h);

        int dasar = h - 40;
        Res.latar(g, tema, kameraX, w, dasar);
        Res.lantai(g, tile, kameraX, dasar, w, h);

        gambarPortal(g, dasar);
        gambarNpc(g, dasar);
        gambarDrop(g, dasar);

        java.util.Enumeration en = ents.elements();
        while (en.hasMoreElements()) {
            Ent e = (Ent) en.nextElement();
            int sx = e.x - kameraX;
            if (sx < -40 || sx > w + 40) {
                continue;
            }
            if (e.jenis == Ent.JENIS_MOB) {
                Res.mob(g, e, sx, dasar);
            } else {
                Res.karakter(g, e, sx, dasar);
            }
            gambarLabel(g, e, sx, dasar);
        }

        gambarHud(g, w, h);
        if (panel != P_TIDAK) {
            gambarPanel(g, w, h);
        }
    }

    private void gambarPortal(Graphics g, int dasar) {
        for (int i = 0; i < portalX.length; i++) {
            int sx = portalX[i] - kameraX;
            g.setColor(0x7BD3F7);
            g.drawRect(sx - 10, dasar - 40, 20, 40);
            g.setColor(0xCFEFFF);
            g.drawString("portal", sx, dasar - 46,
                    Graphics.HCENTER | Graphics.BOTTOM);
        }
    }

    private void gambarNpc(Graphics g, int dasar) {
        for (int i = 0; i < npcX.length; i++) {
            int sx = npcX[i] - kameraX;
            g.setColor(0xE8C46A);
            g.fillRect(sx - 7, dasar - 26, 14, 26);
            g.setColor(0x2C2113);
            g.drawRect(sx - 7, dasar - 26, 14, 26);
            g.setColor(0xFFE9A8);
            g.drawString(npcNama[i], sx, dasar - 30,
                    Graphics.HCENTER | Graphics.BOTTOM);
            if (aku != null && Math.abs(aku.x - npcX[i]) <= 90) {
                g.setColor(0xFFD54A);
                g.drawString("!", sx, dasar - 44,
                        Graphics.HCENTER | Graphics.BOTTOM);
            }
        }
    }

    private void gambarDrop(Graphics g, int dasar) {
        for (int i = 0; i < dropInfo.size(); i++) {
            int[] d = (int[]) dropInfo.elementAt(i);
            int sx = d[3] - kameraX;
            g.setColor(0xFFC24A);
            g.fillRect(sx - 4, dasar - 8, 8, 8);
            g.setColor(0x4A3510);
            g.drawRect(sx - 4, dasar - 8, 8, 8);
        }
    }

    private void gambarLabel(Graphics g, Ent e, int sx, int dasar) {
        int atas = dasar - Res.CELL_H - 12;
        if (e.jenis == Ent.JENIS_MOB) {
            atas = dasar - 34;
        }
        g.setColor(0x000000);
        g.fillRect(sx - 12, atas, 24, 3);
        g.setColor(e.jenis == Ent.JENIS_MOB ? 0xD64545 : 0x5BD672);
        g.fillRect(sx - 12, atas, e.barHp(24), 3);
        g.setColor(0xFFFFFF);
        g.setFont(Font.getFont(Font.FACE_SYSTEM, Font.STYLE_PLAIN,
                Font.SIZE_SMALL));
        if (e.nama != null) {
            g.drawString(e.nama, sx, atas - 2,
                    Graphics.HCENTER | Graphics.BOTTOM);
        }
        if (e.dmgTimer > 0) {
            g.setColor(0xFFE24A);
            g.drawString("-" + e.dmgTeks, sx, atas + e.dmgY - 10,
                    Graphics.HCENTER | Graphics.BOTTOM);
        }
    }

    private void gambarHud(Graphics g, int w, int h) {
        g.setFont(Font.getFont(Font.FACE_SYSTEM, Font.STYLE_PLAIN,
                Font.SIZE_SMALL));
        g.setColor(0x000000);
        g.fillRect(0, 0, w, 26);
        g.setColor(0x2A2118);
        g.fillRect(4, 4, 80, 6);
        g.fillRect(4, 12, 80, 6);
        g.setColor(0xD64545);
        g.fillRect(4, 4, hpMaks > 0 ? hp * 80 / hpMaks : 0, 6);
        g.setColor(0x4A7BD6);
        g.fillRect(4, 12, mpMaks > 0 ? mp * 80 / mpMaks : 0, 6);
        g.setColor(0xFFFFFF);
        g.drawString("Lv" + level + "  " + gold + "g  " + mapNama, 90, 2,
                Graphics.LEFT | Graphics.TOP);
        g.setColor(0x9AA7B4);
        g.drawString("exp " + exp + "/" + expButuh, 90, 13,
                Graphics.LEFT | Graphics.TOP);

        int y = 30;
        g.setColor(0xCBD5E1);
        for (int i = 0; i < chat.size(); i++) {
            g.drawString((String) chat.elementAt(i), 4, y,
                    Graphics.LEFT | Graphics.TOP);
            y += 12;
        }

        if (ajakanEid >= 0) {
            g.setColor(0xFFD54A);
            g.drawString("[6] terima dagang dari " + ajakanNama, 4, h - 26,
                    Graphics.LEFT | Graphics.TOP);
        }
        if (pesanTimer > 0) {
            g.setColor(0xFFE9A8);
            g.drawString(pesanBawah, 4, h - 13, Graphics.LEFT | Graphics.TOP);
        }
    }

    private void kotak(Graphics g, int w, int h, String judul) {
        g.setColor(0x0B0F14);
        g.fillRect(6, 24, w - 12, h - 48);
        g.setColor(0x3E5871);
        g.drawRect(6, 24, w - 12, h - 48);
        g.setColor(0xFFD54A);
        g.drawString(judul, 12, 28, Graphics.LEFT | Graphics.TOP);
        g.setColor(0x8FA3B7);
        g.drawString("2/8 pilih  5 pakai  # tutup", 12, h - 40,
                Graphics.LEFT | Graphics.TOP);
    }

    private void gambarPanel(Graphics g, int w, int h) {
        g.setFont(Font.getFont(Font.FACE_SYSTEM, Font.STYLE_PLAIN,
                Font.SIZE_SMALL));
        if (panel == P_TAS) {
            kotak(g, w, h, "Tas (" + nInv + ")");
            barisTas(g, w, h);
        } else if (panel == P_TOKO) {
            kotak(g, w, h, "Toko - gold " + gold);
            for (int i = 0; i < nToko; i++) {
                g.setColor(i == pilih ? 0xFFD54A : 0xE2E8F0);
                g.drawString(Item.nama(tokoId[i]) + "  " + tokoHarga[i] + "g",
                        14, 44 + i * 12, Graphics.LEFT | Graphics.TOP);
            }
        } else if (panel == P_PARTY) {
            kotak(g, w, h, "Party " + (partyId == 0 ? "-" : ("#" + partyId)));
            for (int i = 0; i < nParty; i++) {
                g.setColor(0xE2E8F0);
                g.drawString(partyNama[i] + "  " + partyHp[i] + "/"
                        + partyHpMaks[i], 14, 44 + i * 12,
                        Graphics.LEFT | Graphics.TOP);
            }
            g.setColor(0x8FA3B7);
            g.drawString("1 buat  3 keluar", 14, 44 + nParty * 12 + 6,
                    Graphics.LEFT | Graphics.TOP);
        } else if (panel == P_SKILL) {
            kotak(g, w, h, "Skill - poin " + poin);
            for (int i = 0; i < skillId.length; i++) {
                g.setColor(i == pilih ? 0xFFD54A : 0xE2E8F0);
                g.drawString("skill " + skillId[i] + " Lv" + skillLv[i], 14,
                        44 + i * 12, Graphics.LEFT | Graphics.TOP);
            }
        } else if (panel == P_QUEST) {
            gambarQuest(g, w, h);
        } else if (panel == P_TRADE) {
            gambarTrade(g, w, h);
        } else if (panel == P_SOSIAL) {
            gambarSosial(g, w, h);
        } else if (panel == P_GUILD) {
            gambarGuild(g, w, h);
        } else if (panel == P_MAIL) {
            gambarMail(g, w, h);
        } else if (panel == P_LELANG) {
            gambarLelang(g, w, h);
        }
    }

    private static final String[] MENU_SOSIAL = {
        "Jurnal quest", "Guild", "Kotak surat", "Papan lelang"
    };

    private void gambarSosial(Graphics g, int w, int h) {
        kotak(g, w, h, "Menu sosial");
        for (int i = 0; i < MENU_SOSIAL.length; i++) {
            g.setColor(i == pilih ? 0xFFD54A : 0xE2E8F0);
            g.drawString(MENU_SOSIAL[i], 14, 44 + i * 12,
                    Graphics.LEFT | Graphics.TOP);
        }
        g.setColor(0x8FA3B7);
        g.drawString("5 pilih   # tutup", 14, 44 + MENU_SOSIAL.length * 12 + 6,
                Graphics.LEFT | Graphics.TOP);
    }

    private void gambarGuild(Graphics g, int w, int h) {
        if (!punyaGuild) {
            kotak(g, w, h, "Guild");
            g.setColor(0xE2E8F0);
            g.drawString("Kamu belum punya guild.", 14, 44,
                    Graphics.LEFT | Graphics.TOP);
            g.setColor(0x8FA3B7);
            if (undanganGid >= 0) {
                g.drawString("Undangan: " + undanganGuild, 14, 60,
                        Graphics.LEFT | Graphics.TOP);
                g.drawString("2 terima undangan", 14, 76,
                        Graphics.LEFT | Graphics.TOP);
            }
            g.drawString("1 dirikan guild (chat: /guild nama)", 14, 92,
                    Graphics.LEFT | Graphics.TOP);
            return;
        }
        kotak(g, w, h, guildNama + " Lv" + guildLevel);
        int y = 44;
        g.setColor(0x8FA3B7);
        g.drawString("exp " + guildExp + "/" + guildExpNaik + "  kas " + guildKas,
                14, y, Graphics.LEFT | Graphics.TOP);
        y += 12;
        g.drawString("bonus exp +" + guildBonusExp + "%  gold +" + guildBonusGold
                + "%", 14, y, Graphics.LEFT | Graphics.TOP);
        y += 12;
        g.drawString("perang menang " + guildMenang + " kalah " + guildKalah,
                14, y, Graphics.LEFT | Graphics.TOP);
        y += 12;
        if (warId != 0) {
            g.setColor(0xFF6B6B);
            g.drawString(warNamaA + " " + warSkorA + " - " + warSkorB + " "
                    + warNamaB + "  sisa " + (warSisa / 60) + "m", 14, y,
                    Graphics.LEFT | Graphics.TOP);
            y += 12;
        }
        y += 4;
        for (int i = 0; i < nAnggota && y < h - 66; i++) {
            g.setColor(i == pilih ? 0xFFD54A : (anggotaOnline[i] ? 0xE2E8F0
                    : 0x6B7A8C));
            g.drawString(anggotaNama[i] + " Lv" + anggotaLevel[i] + " "
                    + namaPangkat(anggotaPangkat[i]) + " (" + anggotaSumbang[i]
                    + "g)", 14, y, Graphics.LEFT | Graphics.TOP);
            y += 12;
        }
        g.setColor(0x8FA3B7);
        g.drawString("1 undang  3 keluar  7 sumbang  9 perang", 14, h - 60,
                Graphics.LEFT | Graphics.TOP);
    }

    private void gambarMail(Graphics g, int w, int h) {
        if (bacaId != 0) {
            kotak(g, w, h, "Surat: " + bacaJudul);
            g.setColor(0x8FA3B7);
            g.drawString("dari " + bacaDari, 14, 44, Graphics.LEFT | Graphics.TOP);
            g.setColor(0xE2E8F0);
            int y = 60;
            String sisa = bacaIsi;
            while (sisa.length() > 0 && y < h - 60) {
                int potong = sisa.length() > 34 ? 34 : sisa.length();
                g.drawString(sisa.substring(0, potong), 14, y,
                        Graphics.LEFT | Graphics.TOP);
                sisa = sisa.substring(potong);
                y += 12;
            }
            g.setColor(0xFFD54A);
            g.drawString("gold " + bacaGold + "  lampiran " + bacaLampiran, 14,
                    y + 4, Graphics.LEFT | Graphics.TOP);
            g.setColor(0x8FA3B7);
            g.drawString("1 ambil  3 hapus  4 kembali", 14, h - 60,
                    Graphics.LEFT | Graphics.TOP);
            return;
        }
        kotak(g, w, h, "Kotak surat (" + nMail + ")");
        int y = 44;
        for (int i = 0; i < nMail && y < h - 66; i++) {
            g.setColor(i == pilih ? 0xFFD54A : (mailDibaca[i] ? 0x8FA3B7
                    : 0xE2E8F0));
            String tanda = mailLampiran[i] > 0 || mailGold[i] > 0 ? "* " : "  ";
            g.drawString(tanda + mailJudul[i] + " - " + mailDari[i], 14, y,
                    Graphics.LEFT | Graphics.TOP);
            y += 12;
        }
        g.setColor(0x8FA3B7);
        g.drawString("5 baca  1 ambil  3 hapus", 14, h - 60,
                Graphics.LEFT | Graphics.TOP);
    }

    private void gambarLelang(Graphics g, int w, int h) {
        kotak(g, w, h, lelangMode == 1 ? "Lapak saya"
                : ("Papan lelang hal " + (lelangHalaman + 1)));
        int y = 44;
        for (int i = 0; i < nLelang && y < h - 66; i++) {
            g.setColor(i == pilih ? 0xFFD54A : 0xE2E8F0);
            g.drawString(Item.namaPlus(lelangItem[i], lelangPlus[i]) + " x"
                    + lelangJumlah[i] + "  " + lelangHarga[i] + "g", 14, y,
                    Graphics.LEFT | Graphics.TOP);
            y += 12;
            g.setColor(0x8FA3B7);
            g.drawString("   " + lelangPenjual[i] + "  sisa "
                    + (lelangSisa[i] / 3600) + "j", 14, y,
                    Graphics.LEFT | Graphics.TOP);
            y += 12;
        }
        g.setColor(0x8FA3B7);
        g.drawString("5 beli  1 lapak saya  3 tarik  4/6 halaman", 14, h - 60,
                Graphics.LEFT | Graphics.TOP);
    }

    private void barisTas(Graphics g, int w, int h) {
        int y = 44;
        for (int i = 0; i < nInv && y < h - 54; i++) {
            g.setColor(i == pilih ? 0xFFD54A : 0xE2E8F0);
            g.drawString(Item.namaPlus(invId[i], invPlus[i]) + " x"
                    + invJumlah[i], 14, y, Graphics.LEFT | Graphics.TOP);
            y += 12;
        }
        g.setColor(0x8FA3B7);
        y += 4;
        for (int i = 0; i < nEq; i++) {
            g.drawString(Item.namaSlotEquip(eqSlot[i]) + ": "
                    + Item.namaPlus(eqId[i], eqPlus[i]), 14, y,
                    Graphics.LEFT | Graphics.TOP);
            y += 12;
        }
    }

    private String kodeQuest(int kode) {
        if (kode == 0) {
            return "[baru]";
        }
        if (kode == 1) {
            return "[jalan]";
        }
        if (kode == 2) {
            return "[siap]";
        }
        if (kode == 3) {
            return "[selesai]";
        }
        return "[terkunci]";
    }

    private void gambarQuest(Graphics g, int w, int h) {
        kotak(g, w, h, questMode == 0 ? "Bicara dengan NPC" : "Jurnal Quest");
        int y = 44;
        for (int i = 0; i < nQuest && y < h - 74; i++) {
            g.setColor(i == pilih ? 0xFFD54A : 0xE2E8F0);
            g.drawString(kodeQuest(questKode[i]) + " " + questNama[i], 14, y,
                    Graphics.LEFT | Graphics.TOP);
            y += 12;
            if (questJenis[i] != 2 && questKode[i] >= 1 && questKode[i] <= 2) {
                g.setColor(0x9AA7B4);
                g.drawString("   " + questProgres[i] + "/" + questButuh[i], 14,
                        y, Graphics.LEFT | Graphics.TOP);
                y += 12;
            }
        }
        if (nQuest == 0) {
            g.setColor(0x9AA7B4);
            g.drawString("belum ada quest di sini", 14, y,
                    Graphics.LEFT | Graphics.TOP);
        } else {
            g.setColor(0xCBD5E1);
            String teks = questTeks[pilih];
            int lebar = w - 28;
            int mulai = 0;
            int baris = 0;
            Font f = g.getFont();
            while (mulai < teks.length() && baris < 3) {
                int akhir = teks.length();
                while (akhir > mulai
                        && f.stringWidth(teks.substring(mulai, akhir)) > lebar) {
                    akhir--;
                }
                g.drawString(teks.substring(mulai, akhir), 14, h - 74 + baris * 12,
                        Graphics.LEFT | Graphics.TOP);
                mulai = akhir;
                baris++;
            }
        }
        g.setColor(0x8FA3B7);
        g.drawString("5 ambil/serah  3 batal  4 jurnal  # tutup", 14, h - 38,
                Graphics.LEFT | Graphics.TOP);
    }

    private void gambarTrade(Graphics g, int w, int h) {
        kotak(g, w, h, "Dagang dengan " + tradeLawan);
        int tengah = w / 2;
        g.setColor(0x3E5871);
        g.drawLine(tengah, 40, tengah, h - 56);

        g.setColor(kunciKamu ? 0x5BD672 : 0xE2E8F0);
        g.drawString("Kamu " + goldKamu + "g" + (kunciKamu ? " [kunci]" : ""),
                14, 42, Graphics.LEFT | Graphics.TOP);
        for (int i = 0; i < nTawarKamu; i++) {
            g.drawString(Item.namaPlus(tawarKamuId[i], tawarKamuPlus[i]) + " x"
                    + tawarKamuJumlah[i], 14, 56 + i * 12,
                    Graphics.LEFT | Graphics.TOP);
        }
        g.setColor(kunciLawan ? 0x5BD672 : 0xE2E8F0);
        g.drawString(tradeLawan + " " + goldLawan + "g"
                + (kunciLawan ? " [kunci]" : ""), tengah + 8, 42,
                Graphics.LEFT | Graphics.TOP);
        for (int i = 0; i < nTawarLawan; i++) {
            g.drawString(Item.namaPlus(tawarLawanId[i], tawarLawanPlus[i]) + " x"
                    + tawarLawanJumlah[i], tengah + 8, 56 + i * 12,
                    Graphics.LEFT | Graphics.TOP);
        }

        int y = h - 56 - 12 * 4;
        g.setColor(0xFFD54A);
        g.drawString("Tas (5 tambah, rencana gold " + rencanaGold + ")", 14,
                y - 12, Graphics.LEFT | Graphics.TOP);
        for (int i = 0; i < nInv && i < 4; i++) {
            int idx = (pilih / 4) * 4 + i;
            if (idx >= nInv) {
                break;
            }
            g.setColor(idx == pilih ? 0xFFD54A : 0xCBD5E1);
            g.drawString(Item.namaPlus(invId[idx], invPlus[idx]) + " x"
                    + invJumlah[idx], 14, y + i * 12,
                    Graphics.LEFT | Graphics.TOP);
        }
        g.setColor(0x8FA3B7);
        g.drawString("5 tawar  1 +100g  3 kosongkan  9 kunci  * batal", 14,
                h - 38, Graphics.LEFT | Graphics.TOP);
    }

    // ------------------------------------------------------------ tombol
    protected void keyPressed(int kode) {
        int aksi = 0;
        try {
            aksi = getGameAction(kode);
        } catch (Exception e) {
        }
        if (panel != P_TIDAK) {
            tombolPanel(kode, aksi);
            return;
        }
        if (kode == KEY_NUM4 || aksi == LEFT) {
            tekanKiri = 1;
            tekanKanan = 0;
            if (kode == KEY_NUM4) {
                bicaraNpc();
                tekanKiri = 0;
            }
            return;
        }
        if (kode == KEY_NUM6 || aksi == RIGHT) {
            if (kode == KEY_NUM6) {
                dagangDekat();
                return;
            }
            tekanKanan = 1;
            tekanKiri = 0;
            return;
        }
        if (kode == KEY_NUM5 || aksi == FIRE) {
            serangTerdekat();
        } else if (kode == KEY_NUM3) {
            ambilDrop();
        } else if (kode == KEY_NUM2 || aksi == UP) {
            lewatPortal();
        } else if (kode == KEY_NUM1) {
            net.kirim(new Msg.Tulis(Msg.C_TOKO).b(0));
        } else if (kode == KEY_NUM7) {
            panel = P_TAS;
            pilih = 0;
        } else if (kode == KEY_NUM8) {
            panel = P_PARTY;
        } else if (kode == KEY_NUM9) {
            panel = P_SKILL;
            pilih = 0;
        } else if (kode == KEY_STAR) {
            panel = P_SOSIAL;
            pilih = 0;
        } else if (kode == KEY_POUND) {
            app.bukaChat();
        } else if (kode == KEY_NUM0) {
            app.bukaMenu();
        }
    }

    protected void keyReleased(int kode) {
        int aksi = 0;
        try {
            aksi = getGameAction(kode);
        } catch (Exception e) {
        }
        if (aksi == LEFT) {
            tekanKiri = 0;
        }
        if (aksi == RIGHT) {
            tekanKanan = 0;
        }
        if (tekanKiri == 0 && tekanKanan == 0 && aku != null) {
            net.kirim(new Msg.Tulis(Msg.C_GERAK).s(langkahX).sb(aku.arah).b(0));
        }
    }

    private void tombolPanel(int kode, int aksi) {
        int jumlah = jumlahBaris();
        if (kode == KEY_NUM8 || aksi == DOWN) {
            if (jumlah > 0) {
                pilih = (pilih + 1) % jumlah;
            }
            return;
        }
        if (kode == KEY_NUM2 || aksi == UP) {
            if (jumlah > 0) {
                pilih = (pilih + jumlah - 1) % jumlah;
            }
            return;
        }
        if (kode == KEY_POUND) {
            panel = P_TIDAK;
            return;
        }
        if (panel == P_QUEST) {
            tombolQuest(kode, aksi);
        } else if (panel == P_TRADE) {
            tombolTrade(kode, aksi);
        } else if (panel == P_SOSIAL) {
            tombolSosial(kode, aksi);
        } else if (panel == P_GUILD) {
            tombolGuild(kode, aksi);
        } else if (panel == P_MAIL) {
            tombolMail(kode, aksi);
        } else if (panel == P_LELANG) {
            tombolLelang(kode, aksi);
        } else if (panel == P_TAS) {
            if (kode == KEY_NUM5 || aksi == FIRE) {
                if (pilih < nInv) {
                    if (Item.bisaDiminum(invId[pilih])) {
                        net.kirim(new Msg.Tulis(Msg.C_PAKAI_ITEM).b(invSlot[pilih]));
                    } else if (Item.bisaDipakai(invId[pilih])) {
                        net.kirim(new Msg.Tulis(Msg.C_PAKAI_EQUIP).b(invSlot[pilih]));
                    }
                }
            } else if (kode == KEY_NUM1 && pilih < nInv) {
                net.kirim(new Msg.Tulis(Msg.C_TOKO).b(2).b(invSlot[pilih]).us(1));
            } else if (kode == KEY_NUM3 && pilih < nInv) {
                net.kirim(new Msg.Tulis(Msg.C_UPGRADE).b(invSlot[pilih]));
            } else if (kode == KEY_NUM9 && pilih < nEq) {
                net.kirim(new Msg.Tulis(Msg.C_LEPAS_EQUIP).b(eqSlot[pilih]));
            } else if (kode == KEY_STAR && pilih < nInv) {
                // pasang 1 buah ke papan lelang dengan harga dasar 1000 gold
                pasangLelang(invSlot[pilih], 1000);
                info("lapak dipasang 1000g - ubah lewat chat /lapak");
            }
        } else if (panel == P_TOKO) {
            if (kode == KEY_NUM5 || aksi == FIRE) {
                if (pilih < nToko) {
                    net.kirim(new Msg.Tulis(Msg.C_TOKO).b(1).us(tokoId[pilih]).us(1));
                }
            }
        } else if (panel == P_PARTY) {
            if (kode == KEY_NUM1) {
                net.kirim(new Msg.Tulis(Msg.C_PARTY).b(0));
            } else if (kode == KEY_NUM3) {
                net.kirim(new Msg.Tulis(Msg.C_PARTY).b(2));
            }
        } else if (panel == P_SKILL) {
            if ((kode == KEY_NUM5 || aksi == FIRE) && pilih < skillId.length) {
                net.kirim(new Msg.Tulis(Msg.C_NAIK_SKILL).us(skillId[pilih]));
            }
        }
    }

    private int jumlahBaris() {
        if (panel == P_TAS || panel == P_TRADE) {
            return nInv;
        }
        if (panel == P_TOKO) {
            return nToko;
        }
        if (panel == P_SKILL) {
            return skillId.length;
        }
        if (panel == P_QUEST) {
            return nQuest;
        }
        if (panel == P_SOSIAL) {
            return MENU_SOSIAL.length;
        }
        if (panel == P_GUILD) {
            return nAnggota;
        }
        if (panel == P_MAIL) {
            return bacaId != 0 ? 0 : nMail;
        }
        if (panel == P_LELANG) {
            return nLelang;
        }
        return 0;
    }

    private void tombolSosial(int kode, int aksi) {
        if (kode == KEY_NUM5 || aksi == FIRE) {
            if (pilih == 0) {
                net.kirim(new Msg.Tulis(Msg.C_QUEST).b(4));
            } else if (pilih == 1) {
                net.kirim(new Msg.Tulis(Msg.C_GUILD).b(7));
                panel = P_GUILD;
                pilih = 0;
            } else if (pilih == 2) {
                net.kirim(new Msg.Tulis(Msg.C_MAIL).b(0));
                panel = P_MAIL;
                pilih = 0;
            } else {
                lelangHalaman = 0;
                net.kirim(new Msg.Tulis(Msg.C_LELANG).b(0).us(0).b(0));
            }
        }
    }

    private void tombolGuild(int kode, int aksi) {
        if (!punyaGuild) {
            if (kode == KEY_NUM2 && undanganGid >= 0) {
                net.kirim(new Msg.Tulis(Msg.C_GUILD).b(2).i(undanganGid));
                undanganGid = -1;
            } else if (kode == KEY_NUM1) {
                app.bukaChat();
                info("ketik: /guild NamaGuild");
            }
            return;
        }
        if (kode == KEY_NUM1) {
            Ent target = pemainTerdekat();
            if (target == null) {
                info("dekati pemain yang mau diundang");
            } else {
                net.kirim(new Msg.Tulis(Msg.C_GUILD).b(1).i(target.eid));
                info("undangan dikirim ke " + target.nama);
            }
        } else if (kode == KEY_NUM3) {
            net.kirim(new Msg.Tulis(Msg.C_GUILD).b(3));
        } else if (kode == KEY_NUM7) {
            net.kirim(new Msg.Tulis(Msg.C_GUILD).b(6).i(1000));
            info("menyumbang 1000 gold ke kas guild");
        } else if (kode == KEY_NUM9) {
            if (tantanganDari.length() > 0) {
                net.kirim(new Msg.Tulis(Msg.C_GUILD).b(10));
                tantanganDari = "";
            } else {
                app.bukaChat();
                info("ketik: /war NamaGuild taruhan");
            }
        } else if (kode == KEY_STAR) {
            net.kirim(new Msg.Tulis(Msg.C_GUILD).b(12));
        } else if ((kode == KEY_NUM5 || aksi == FIRE) && pilih < nAnggota
                && guildPangkatKamu == 2) {
            net.kirim(new Msg.Tulis(Msg.C_GUILD).b(4).i(anggotaId[pilih]));
        }
    }

    private void tombolMail(int kode, int aksi) {
        if (bacaId != 0) {
            if (kode == KEY_NUM1) {
                net.kirim(new Msg.Tulis(Msg.C_MAIL).b(2).i(bacaId));
            } else if (kode == KEY_NUM3) {
                net.kirim(new Msg.Tulis(Msg.C_MAIL).b(3).i(bacaId));
                bacaId = 0;
            } else if (kode == KEY_NUM4 || aksi == LEFT) {
                bacaId = 0;
                net.kirim(new Msg.Tulis(Msg.C_MAIL).b(0));
            }
            return;
        }
        if (nMail == 0) {
            return;
        }
        if (kode == KEY_NUM5 || aksi == FIRE) {
            net.kirim(new Msg.Tulis(Msg.C_MAIL).b(1).i(mailId[pilih]));
        } else if (kode == KEY_NUM1) {
            net.kirim(new Msg.Tulis(Msg.C_MAIL).b(2).i(mailId[pilih]));
        } else if (kode == KEY_NUM3) {
            net.kirim(new Msg.Tulis(Msg.C_MAIL).b(3).i(mailId[pilih]));
        }
    }

    private void tombolLelang(int kode, int aksi) {
        if (kode == KEY_NUM1) {
            net.kirim(new Msg.Tulis(Msg.C_LELANG).b(1));
            return;
        }
        if (kode == KEY_NUM4 || aksi == LEFT) {
            if (lelangHalaman > 0) {
                lelangHalaman--;
            }
            net.kirim(new Msg.Tulis(Msg.C_LELANG).b(0).us(0).b(lelangHalaman));
            return;
        }
        if (kode == KEY_NUM6 || aksi == RIGHT) {
            lelangHalaman++;
            net.kirim(new Msg.Tulis(Msg.C_LELANG).b(0).us(0).b(lelangHalaman));
            return;
        }
        if (nLelang == 0) {
            return;
        }
        if (kode == KEY_NUM5 || aksi == FIRE) {
            net.kirim(new Msg.Tulis(Msg.C_LELANG).b(3).i(lelangId[pilih]));
        } else if (kode == KEY_NUM3) {
            net.kirim(new Msg.Tulis(Msg.C_LELANG).b(4).i(lelangId[pilih]));
        }
    }

    /** Pasang barang tas ke papan lelang: dipanggil dari panel tas. */
    private void pasangLelang(int slot, int harga) {
        net.kirim(new Msg.Tulis(Msg.C_LELANG).b(2).b(slot).us(1).i(harga));
    }

    private Ent pemainTerdekat() {
        if (aku == null) {
            return null;
        }
        Ent target = null;
        int jarak = 121;
        java.util.Enumeration en = ents.elements();
        while (en.hasMoreElements()) {
            Ent e = (Ent) en.nextElement();
            if (e.jenis != Ent.JENIS_PEMAIN || e.eid == myEid) {
                continue;
            }
            int d = Math.abs(e.x - aku.x);
            if (d < jarak) {
                jarak = d;
                target = e;
            }
        }
        return target;
    }

    private void tombolQuest(int kode, int aksi) {
        if (nQuest == 0) {
            return;
        }
        int qid = questId[pilih];
        if (kode == KEY_NUM5 || aksi == FIRE) {
            int k = questKode[pilih];
            if (k == 0) {
                net.kirim(new Msg.Tulis(Msg.C_QUEST).b(1).us(qid));
            } else if (k == 2) {
                net.kirim(new Msg.Tulis(Msg.C_QUEST).b(2).us(qid));
            } else {
                info("belum bisa: " + kodeQuest(k));
            }
        } else if (kode == KEY_NUM3) {
            net.kirim(new Msg.Tulis(Msg.C_QUEST).b(3).us(qid));
        } else if (kode == KEY_NUM4) {
            net.kirim(new Msg.Tulis(Msg.C_QUEST).b(4));
        }
    }

    private void tombolTrade(int kode, int aksi) {
        if (kode == KEY_NUM5 || aksi == FIRE) {
            if (pilih < nInv && nRencana < rencanaSlot.length) {
                tambahRencana(invSlot[pilih], 1);
                kirimTawaran();
            }
        } else if (kode == KEY_NUM1) {
            rencanaGold += 100;
            if (rencanaGold > gold) {
                rencanaGold = gold;
            }
            kirimTawaran();
        } else if (kode == KEY_NUM3) {
            nRencana = 0;
            rencanaGold = 0;
            kirimTawaran();
        } else if (kode == KEY_NUM9) {
            net.kirim(new Msg.Tulis(Msg.C_TRADE).b(4));
        } else if (kode == KEY_STAR) {
            net.kirim(new Msg.Tulis(Msg.C_TRADE).b(2));
        }
    }

    private void tambahRencana(int slot, int jumlah) {
        for (int i = 0; i < nRencana; i++) {
            if (rencanaSlot[i] == slot) {
                rencanaJumlah[i] += jumlah;
                return;
            }
        }
        rencanaSlot[nRencana] = slot;
        rencanaJumlah[nRencana] = jumlah;
        nRencana++;
    }

    private void kirimTawaran() {
        Msg.Tulis t = new Msg.Tulis(Msg.C_TRADE).b(3).i(rencanaGold).b(nRencana);
        for (int i = 0; i < nRencana; i++) {
            t.b(rencanaSlot[i]).us(rencanaJumlah[i]);
        }
        net.kirim(t);
    }

    // ------------------------------------------------------------ aksi
    private void serangTerdekat() {
        if (aku == null) {
            return;
        }
        Ent target = null;
        int jarakTerbaik = 200;
        java.util.Enumeration en = ents.elements();
        while (en.hasMoreElements()) {
            Ent e = (Ent) en.nextElement();
            if (e.jenis != Ent.JENIS_MOB || !e.hidup) {
                continue;
            }
            int d = Math.abs(e.x - aku.x);
            if (d < jarakTerbaik) {
                jarakTerbaik = d;
                target = e;
            }
        }
        if (target == null) {
            info("tidak ada sasaran");
            return;
        }
        aku.arah = target.x >= aku.x ? 1 : -1;
        aku.setAnim(Ent.ANIM_SERANG);
        net.kirim(new Msg.Tulis(Msg.C_SERANG).us(0).i(target.eid));
    }

    private void ambilDrop() {
        if (aku == null) {
            return;
        }
        for (int i = 0; i < dropInfo.size(); i++) {
            int[] d = (int[]) dropInfo.elementAt(i);
            if (Math.abs(d[3] - aku.x) <= 48) {
                int did = ((Integer) dropId.elementAt(i)).intValue();
                net.kirim(new Msg.Tulis(Msg.C_AMBIL).i(did));
                return;
            }
        }
        info("tidak ada barang di dekatmu");
    }

    private void lewatPortal() {
        if (aku == null) {
            return;
        }
        for (int i = 0; i < portalX.length; i++) {
            if (Math.abs(portalX[i] - aku.x) <= 60) {
                net.kirim(new Msg.Tulis(Msg.C_PINDAH_MAP).b(i));
                return;
            }
        }
        info("tidak ada portal di dekatmu");
    }

    /** Tombol 4: bicara dengan NPC terdekat untuk membuka daftar quest. */
    private void bicaraNpc() {
        if (aku == null) {
            return;
        }
        int terbaik = -1;
        int jarak = 91;
        for (int i = 0; i < npcX.length; i++) {
            int d = Math.abs(npcX[i] - aku.x);
            if (d < jarak) {
                jarak = d;
                terbaik = i;
            }
        }
        if (terbaik < 0) {
            net.kirim(new Msg.Tulis(Msg.C_QUEST).b(4));   // buka jurnal saja
            return;
        }
        net.kirim(new Msg.Tulis(Msg.C_QUEST).b(0).b(terbaik));
    }

    /** Tombol 6: terima ajakan dagang, atau ajak pemain terdekat. */
    private void dagangDekat() {
        if (ajakanEid >= 0) {
            net.kirim(new Msg.Tulis(Msg.C_TRADE).b(1));
            ajakanEid = -1;
            return;
        }
        if (aku == null) {
            return;
        }
        Ent target = null;
        int jarak = 121;
        java.util.Enumeration en = ents.elements();
        while (en.hasMoreElements()) {
            Ent e = (Ent) en.nextElement();
            if (e.jenis != Ent.JENIS_PEMAIN || e.eid == myEid) {
                continue;
            }
            int d = Math.abs(e.x - aku.x);
            if (d < jarak) {
                jarak = d;
                target = e;
            }
        }
        if (target == null) {
            info("tidak ada pemain di dekatmu");
            return;
        }
        net.kirim(new Msg.Tulis(Msg.C_TRADE).b(0).i(target.eid));
        info("mengajak " + target.nama + " berdagang");
    }
}
