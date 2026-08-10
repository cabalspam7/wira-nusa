import java.io.IOException;
import javax.microedition.lcdui.Alert;
import javax.microedition.lcdui.AlertType;
import javax.microedition.lcdui.ChoiceGroup;
import javax.microedition.lcdui.Command;
import javax.microedition.lcdui.CommandListener;
import javax.microedition.lcdui.Display;
import javax.microedition.lcdui.Displayable;
import javax.microedition.lcdui.Form;
import javax.microedition.lcdui.List;
import javax.microedition.lcdui.TextField;
import javax.microedition.midlet.MIDlet;

/**
 * MIDlet WIRA NUSA.
 *
 * Bagian menu (login, daftar, pilih karakter, chat) memakai LCDUI Form
 * biasa supaya ringan dan enak dipakai di HP dengan keypad. Begitu masuk
 * dunia, kendali berpindah ke GameScr yang menggambar sendiri.
 *
 * Paket sebelum masuk dunia dibaca oleh thread menu di kelas ini. Thread
 * itu dimatikan tepat sebelum mengirim PILIH_CHAR supaya paket masuk map
 * tidak direbut dari GameScr.
 */
public final class Main extends MIDlet implements CommandListener, Net.Pendengar {

    private Display display;
    private Net net;
    private GameScr game;
    private Thread menuThread;
    private boolean menuJalan;

    // form login
    private Form formLogin;
    private TextField fHost;
    private TextField fPort;
    private TextField fAkun;
    private TextField fSandi;
    private final Command cmdMasuk = new Command("Masuk", Command.OK, 1);
    private final Command cmdDaftar = new Command("Daftar", Command.SCREEN, 2);
    private final Command cmdKeluar = new Command("Keluar", Command.EXIT, 9);

    // pilih karakter
    private List listChar;
    private int[] charId = new int[0];
    private String[] charNama = new String[0];
    private int[] charJob = new int[0];
    private int[] charRambut = new int[0];
    private int[] charKulit = new int[0];
    private final Command cmdPilih = new Command("Main", Command.OK, 1);
    private final Command cmdBuat = new Command("Buat baru", Command.SCREEN, 2);

    // buat karakter
    private Form formBuat;
    private TextField fNama;
    private ChoiceGroup cgJob;
    private ChoiceGroup cgRambut;
    private ChoiceGroup cgKulit;
    private final Command cmdSimpan = new Command("Buat", Command.OK, 1);
    private final Command cmdBatal = new Command("Batal", Command.BACK, 2);

    // chat
    private Form formChat;
    private TextField fChat;
    private final Command cmdKirim = new Command("Kirim", Command.OK, 1);

    // menu dalam game
    private List listMenu;
    private final Command cmdTutup = new Command("Tutup", Command.BACK, 2);

    public String namaKarakter = "";
    public int jobKarakter;
    public int rambutKarakter;
    public int kulitKarakter;

    protected void startApp() {
        if (display == null) {
            display = Display.getDisplay(this);
            Cache.muat();
            bangunLogin();
        }
        if (game != null) {
            display.setCurrent(game);
            game.mulai();
        } else {
            display.setCurrent(formLogin);
        }
    }

    protected void pauseApp() {
        if (game != null) {
            game.berhenti();
        }
    }

    protected void destroyApp(boolean tanpaSyarat) {
        menuJalan = false;
        if (game != null) {
            game.berhenti();
        }
        if (net != null) {
            net.putus("keluar");
        }
        Cache.simpan();
    }

    // ------------------------------------------------------------ layar
    private void bangunLogin() {
        formLogin = new Form("WIRA NUSA");
        fHost = new TextField("Server", Cache.host, 40, TextField.ANY);
        fPort = new TextField("Port", "" + Cache.port, 6, TextField.NUMERIC);
        fAkun = new TextField("Akun", Cache.akun, 14, TextField.ANY);
        fSandi = new TextField("Sandi", "", 32, TextField.PASSWORD);
        formLogin.append(fHost);
        formLogin.append(fPort);
        formLogin.append(fAkun);
        formLogin.append(fSandi);
        formLogin.addCommand(cmdMasuk);
        formLogin.addCommand(cmdDaftar);
        formLogin.addCommand(cmdKeluar);
        formLogin.setCommandListener(this);
    }

    private void tampilkanPesan(String judul, String isi) {
        Alert a = new Alert(judul, isi, null, AlertType.INFO);
        a.setTimeout(2000);
        display.setCurrent(a);
    }

    private boolean sambungKalauPerlu() {
        if (net != null && net.tersambung()) {
            return true;
        }
        Cache.host = fHost.getString().trim();
        try {
            Cache.port = Integer.parseInt(fPort.getString().trim());
        } catch (NumberFormatException e) {
            Cache.port = 7777;
        }
        Cache.akun = fAkun.getString().trim();
        Cache.simpan();
        net = new Net(this);
        try {
            net.sambung(Cache.host, Cache.port);
        } catch (IOException e) {
            tampilkanPesan("Gagal", "tidak bisa menyambung ke " + Cache.host
                    + ":" + Cache.port);
            return false;
        } catch (SecurityException e) {
            tampilkanPesan("Ditolak", "izin jaringan ditolak di HP ini");
            return false;
        }
        mulaiThreadMenu();
        return true;
    }

    private void mulaiThreadMenu() {
        menuJalan = true;
        menuThread = new Thread(new Runnable() {
            public void run() {
                while (menuJalan) {
                    Msg.Baca r = net.ambil();
                    while (r != null && menuJalan) {
                        tanganiMenu(r);
                        r = net.ambil();
                    }
                    try {
                        Thread.sleep(60);
                    } catch (InterruptedException e) {
                    }
                }
            }
        });
        menuThread.start();
    }

    private void tanganiMenu(Msg.Baca r) {
        int op = r.opcode;
        if (op == Msg.S_LOGIN_OK) {
            r.teks();
        } else if (op == Msg.S_TOLAK || op == Msg.S_PESAN) {
            final String teks = r.teks();
            tampilkanPesan(op == Msg.S_TOLAK ? "Ditolak" : "Info", teks);
        } else if (op == Msg.S_DAFTAR_CHAR) {
            int n = r.b();
            charId = new int[n];
            charNama = new String[n];
            charJob = new int[n];
            charRambut = new int[n];
            charKulit = new int[n];
            String[] baris = new String[n];
            for (int i = 0; i < n; i++) {
                charId[i] = r.i();
                charNama[i] = r.teks();
                charJob[i] = r.b();
                int lv = r.s();
                charRambut[i] = r.b();
                charKulit[i] = r.b();
                r.b();
                baris[i] = charNama[i] + "  " + Item.namaJob(charJob[i])
                        + " Lv" + lv;
            }
            listChar = new List("Pilih Karakter", List.IMPLICIT, baris, null);
            listChar.addCommand(cmdPilih);
            listChar.addCommand(cmdBuat);
            listChar.addCommand(cmdKeluar);
            listChar.setCommandListener(this);
            display.setCurrent(listChar);
        }
    }

    private void bangunFormBuat() {
        formBuat = new Form("Karakter Baru");
        fNama = new TextField("Nama", "", 14, TextField.ANY);
        cgJob = new ChoiceGroup("Job", ChoiceGroup.EXCLUSIVE, new String[] {
            "Pedang - tahan pukul",
            "Sepasang - cepat",
            "Dukun - sihir & sembuh",
            "Senapan - jarak jauh"
        }, null);
        cgRambut = new ChoiceGroup("Rambut", ChoiceGroup.EXCLUSIVE,
                new String[] {"1", "2", "3", "4"}, null);
        cgKulit = new ChoiceGroup("Kulit", ChoiceGroup.EXCLUSIVE,
                new String[] {"1", "2", "3", "4"}, null);
        formBuat.append(fNama);
        formBuat.append(cgJob);
        formBuat.append(cgRambut);
        formBuat.append(cgKulit);
        formBuat.addCommand(cmdSimpan);
        formBuat.addCommand(cmdBatal);
        formBuat.setCommandListener(this);
    }

    public void bukaChat() {
        if (formChat == null) {
            formChat = new Form("Chat");
            fChat = new TextField("Pesan", "", 120, TextField.ANY);
            formChat.append(fChat);
            formChat.addCommand(cmdKirim);
            formChat.addCommand(cmdBatal);
            formChat.setCommandListener(this);
        }
        display.setCurrent(formChat);
    }

    public void bukaMenu() {
        listMenu = new List("Menu", List.IMPLICIT, new String[] {
            "Lanjut main", "Chat", "Ganti karakter", "Keluar game"
        }, null);
        listMenu.addCommand(cmdTutup);
        listMenu.setCommandListener(this);
        display.setCurrent(listMenu);
    }

    private void kembaliKeGame() {
        if (game != null) {
            display.setCurrent(game);
            game.mulai();
        }
    }

    // --------------------------------------------------------- perintah
    public void commandAction(Command c, Displayable d) {
        if (c == cmdKeluar) {
            destroyApp(true);
            notifyDestroyed();
            return;
        }
        if (d == formLogin) {
            if (c == cmdMasuk || c == cmdDaftar) {
                if (!sambungKalauPerlu()) {
                    return;
                }
                String akun = fAkun.getString().trim();
                String sandi = fSandi.getString();
                int op = (c == cmdMasuk) ? Msg.C_LOGIN : Msg.C_DAFTAR;
                net.kirim(new Msg.Tulis(op).teks(akun).teks(sandi));
            }
            return;
        }
        if (d == listChar) {
            if (c == cmdBuat) {
                bangunFormBuat();
                display.setCurrent(formBuat);
                return;
            }
            int idx = listChar.getSelectedIndex();
            if (idx < 0 || idx >= charId.length) {
                return;
            }
            namaKarakter = charNama[idx];
            jobKarakter = charJob[idx];
            rambutKarakter = charRambut[idx];
            kulitKarakter = charKulit[idx];
            menuJalan = false;          // serahkan antrian paket ke GameScr
            try {
                Thread.sleep(120);
            } catch (InterruptedException e) {
            }
            game = new GameScr(this, net);
            display.setCurrent(game);
            game.mulai();
            net.kirim(new Msg.Tulis(Msg.C_PILIH_CHAR).i(charId[idx]));
            return;
        }
        if (d == formBuat) {
            if (c == cmdBatal) {
                display.setCurrent(listChar);
                return;
            }
            String nama = fNama.getString().trim();
            if (nama.length() < 3) {
                tampilkanPesan("Nama", "minimal 3 huruf");
                return;
            }
            net.kirim(new Msg.Tulis(Msg.C_BUAT_CHAR).teks(nama)
                    .b(cgJob.getSelectedIndex())
                    .b(cgRambut.getSelectedIndex())
                    .b(cgKulit.getSelectedIndex()));
            return;
        }
        if (d == formChat) {
            if (c == cmdKirim && game != null) {
                game.kirimChat(fChat.getString());
                fChat.setString("");
            }
            kembaliKeGame();
            return;
        }
        if (d == listMenu) {
            int idx = listMenu.getSelectedIndex();
            if (c == cmdTutup || idx == 0) {
                kembaliKeGame();
            } else if (idx == 1) {
                bukaChat();
            } else if (idx == 2) {
                if (game != null) {
                    game.berhenti();
                    game = null;
                }
                if (net != null) {
                    net.putus("ganti karakter");
                }
                net = null;
                display.setCurrent(formLogin);
            } else if (idx == 3) {
                destroyApp(true);
                notifyDestroyed();
            }
        }
    }

    // ----------------------------------------------------- dari jaringan
    public void onPaket(Msg.Baca r) {
        // tidak dipakai: paket diambil lewat antrian (net.ambil)
    }

    public void onPutus(String alasan) {
        menuJalan = false;
        if (game != null) {
            game.berhenti();
            game = null;
        }
        if (display != null) {
            Alert a = new Alert("Terputus", alasan, null, AlertType.ERROR);
            a.setTimeout(3000);
            display.setCurrent(a, formLogin);
        }
    }
}
