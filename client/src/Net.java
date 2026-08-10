import java.io.DataInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.util.Vector;
import javax.microedition.io.Connector;
import javax.microedition.io.StreamConnection;

/**
 * Koneksi socket ke server WIRA NUSA.
 *
 * Satu thread pembaca menaruh paket ke antrian; game loop mengambilnya
 * di thread render supaya tidak ada masalah sinkronisasi di layar.
 * Penulisan paket dikunci karena bisa dipanggil dari thread mana saja.
 */
public final class Net implements Runnable {

    public interface Pendengar {
        void onPaket(Msg.Baca r);

        void onPutus(String alasan);
    }

    private StreamConnection kon;
    private DataInputStream in;
    private OutputStream out;
    private final Vector antrian = new Vector();
    private final Pendengar pendengar;
    private boolean jalan;
    private final Object kunciKirim = new Object();

    public Net(Pendengar pendengar) {
        this.pendengar = pendengar;
    }

    public boolean tersambung() {
        return jalan;
    }

    public void sambung(String host, int port) throws IOException {
        kon = (StreamConnection) Connector.open("socket://" + host + ":" + port,
                Connector.READ_WRITE, true);
        in = kon.openDataInputStream();
        out = kon.openOutputStream();
        jalan = true;
        new Thread(this).start();
    }

    public void kirim(Msg.Tulis t) {
        if (!jalan) {
            return;
        }
        byte[] paket = t.paket();
        synchronized (kunciKirim) {
            try {
                out.write(paket);
                out.flush();
            } catch (IOException e) {
                putus("gagal kirim");
            }
        }
    }

    /** Ambil satu paket dari antrian, atau null kalau kosong. */
    public Msg.Baca ambil() {
        synchronized (antrian) {
            if (antrian.isEmpty()) {
                return null;
            }
            Msg.Baca r = (Msg.Baca) antrian.elementAt(0);
            antrian.removeElementAt(0);
            return r;
        }
    }

    public void run() {
        try {
            while (jalan) {
                int hi = in.read();
                if (hi < 0) {
                    break;
                }
                int lo = in.read();
                if (lo < 0) {
                    break;
                }
                int panjang = ((hi & 0xFF) << 8) | (lo & 0xFF);
                if (panjang < 1 || panjang > 8192) {
                    putus("paket tidak masuk akal");
                    return;
                }
                int opcode = in.read();
                if (opcode < 0) {
                    break;
                }
                byte[] isi = new byte[panjang - 1];
                in.readFully(isi);
                Msg.Baca r = new Msg.Baca(opcode, isi);
                synchronized (antrian) {
                    antrian.addElement(r);
                }
            }
            putus("koneksi ditutup server");
        } catch (IOException e) {
            putus("koneksi terputus");
        } catch (Exception e) {
            putus("kesalahan jaringan");
        }
    }

    public void putus(String alasan) {
        if (!jalan) {
            return;
        }
        jalan = false;
        try {
            if (in != null) {
                in.close();
            }
            if (out != null) {
                out.close();
            }
            if (kon != null) {
                kon.close();
            }
        } catch (IOException e) {
        }
        if (pendengar != null) {
            pendengar.onPutus(alasan);
        }
    }
}
