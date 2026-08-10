#!/usr/bin/env python3
"""Membuat stub javax.microedition.* supaya client bisa DICOMPILE tanpa WTK.

Stub ini HANYA untuk compile. Saat mem-package jar, kelas stub tidak
ikut dimasukkan -- yang dipakai di HP/emulator adalah implementasi MIDP
asli milik emulator. Jadi isi method sengaja kosong.

    python3 tools/gen_stubs.py

Keluaran: client/stubs/javax/microedition/**/*.java  lalu STUB_OK
"""

import os
import sys

AKAR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "client", "stubs")

CATATAN = ("// Stub kompilasi WIRA NUSA. Bukan implementasi MIDP.\n"
           "// Jangan dimasukkan ke dalam jar akhir.\n")

FILE = {}


def tulis(paket, nama, isi):
    FILE[(paket, nama)] = isi


# ------------------------------------------------------------- midlet
tulis("javax.microedition.midlet", "MIDletStateChangeException", """
public class MIDletStateChangeException extends Exception {
    public MIDletStateChangeException() { }
    public MIDletStateChangeException(String s) { super(s); }
}
""")

tulis("javax.microedition.midlet", "MIDlet", """
public abstract class MIDlet {
    protected MIDlet() { }
    protected abstract void startApp() throws MIDletStateChangeException;
    protected abstract void pauseApp();
    protected abstract void destroyApp(boolean unconditional)
            throws MIDletStateChangeException;
    public final void notifyDestroyed() { }
    public final void notifyPaused() { }
    public final String getAppProperty(String key) { return null; }
    public final void resumeRequest() { }
    public final boolean platformRequest(String url) { return false; }
}
""")

# --------------------------------------------------------------- lcdui
tulis("javax.microedition.lcdui", "Command", """
public class Command {
    public static final int SCREEN = 1;
    public static final int BACK = 2;
    public static final int CANCEL = 3;
    public static final int OK = 4;
    public static final int HELP = 5;
    public static final int STOP = 6;
    public static final int EXIT = 7;
    public static final int ITEM = 8;
    public Command(String label, int commandType, int priority) { }
    public Command(String label, String longLabel, int type, int pri) { }
    public String getLabel() { return null; }
    public int getCommandType() { return 0; }
    public int getPriority() { return 0; }
}
""")

tulis("javax.microedition.lcdui", "CommandListener", """
public interface CommandListener {
    void commandAction(Command c, Displayable d);
}
""")

tulis("javax.microedition.lcdui", "Displayable", """
public abstract class Displayable {
    public void addCommand(Command cmd) { }
    public void removeCommand(Command cmd) { }
    public void setCommandListener(CommandListener l) { }
    public int getWidth() { return 240; }
    public int getHeight() { return 320; }
    public boolean isShown() { return false; }
    public String getTitle() { return null; }
    public void setTitle(String s) { }
    protected void sizeChanged(int w, int h) { }
}
""")

tulis("javax.microedition.lcdui", "Display", """
import javax.microedition.midlet.MIDlet;

public class Display {
    private Display() { }
    public static Display getDisplay(MIDlet m) { return new Display(); }
    public void setCurrent(Displayable next) { }
    public void setCurrent(Alert alert, Displayable next) { }
    public Displayable getCurrent() { return null; }
    public boolean flashBacklight(int ms) { return false; }
    public boolean vibrate(int ms) { return false; }
    public int numColors() { return 65536; }
    public boolean isColor() { return true; }
    public void callSerially(Runnable r) { }
}
""")

tulis("javax.microedition.lcdui", "Item", """
public abstract class Item {
    public static final int PLAIN = 0;
    public static final int HYPERLINK = 1;
    public static final int BUTTON = 2;
    public String getLabel() { return null; }
    public void setLabel(String label) { }
    public void addCommand(Command cmd) { }
    public void setDefaultCommand(Command cmd) { }
}
""")

tulis("javax.microedition.lcdui", "Screen", """
public abstract class Screen extends Displayable {
}
""")

tulis("javax.microedition.lcdui", "Form", """
public class Form extends Screen {
    public Form(String title) { }
    public Form(String title, Item[] items) { }
    public int append(Item item) { return 0; }
    public int append(String str) { return 0; }
    public int append(Image img) { return 0; }
    public void insert(int index, Item item) { }
    public void delete(int index) { }
    public void deleteAll() { }
    public void set(int index, Item item) { }
    public Item get(int index) { return null; }
    public int size() { return 0; }
}
""")

tulis("javax.microedition.lcdui", "StringItem", """
public class StringItem extends Item {
    public StringItem(String label, String text) { }
    public StringItem(String label, String text, int appearanceMode) { }
    public String getText() { return null; }
    public void setText(String text) { }
}
""")

tulis("javax.microedition.lcdui", "TextField", """
public class TextField extends Item {
    public static final int ANY = 0;
    public static final int EMAILADDR = 1;
    public static final int NUMERIC = 2;
    public static final int PHONENUMBER = 3;
    public static final int URL = 4;
    public static final int DECIMAL = 5;
    public static final int PASSWORD = 0x10000;
    public static final int UNEDITABLE = 0x20000;
    public TextField(String label, String text, int maxSize, int constraints) { }
    public String getString() { return \"\"; }
    public void setString(String text) { }
    public int getMaxSize() { return 0; }
    public int size() { return 0; }
    public void setConstraints(int constraints) { }
}
""")

tulis("javax.microedition.lcdui", "Choice", """
public interface Choice {
    int EXCLUSIVE = 1;
    int MULTIPLE = 2;
    int IMPLICIT = 3;
    int POPUP = 4;
    int TEXT_WRAP_DEFAULT = 0;
    int TEXT_WRAP_ON = 1;
    int TEXT_WRAP_OFF = 2;
    int size();
    String getString(int elementNum);
    int append(String stringPart, Image imagePart);
    void delete(int elementNum);
    void deleteAll();
    boolean isSelected(int elementNum);
    int getSelectedIndex();
    void setSelectedIndex(int elementNum, boolean selected);
}
""")

tulis("javax.microedition.lcdui", "ChoiceGroup", """
public class ChoiceGroup extends Item implements Choice {
    public ChoiceGroup(String label, int choiceType) { }
    public ChoiceGroup(String label, int choiceType, String[] stringElements,
            Image[] imageElements) { }
    public int size() { return 0; }
    public String getString(int elementNum) { return null; }
    public int append(String stringPart, Image imagePart) { return 0; }
    public void delete(int elementNum) { }
    public void deleteAll() { }
    public boolean isSelected(int elementNum) { return false; }
    public int getSelectedIndex() { return 0; }
    public void setSelectedIndex(int elementNum, boolean selected) { }
    public int getSelectedFlags(boolean[] flags) { return 0; }
}
""")

tulis("javax.microedition.lcdui", "List", """
public class List extends Screen implements Choice {
    public static final Command SELECT_COMMAND =
            new Command(\"\", Command.SCREEN, 0);
    public static final int EXCLUSIVE = Choice.EXCLUSIVE;
    public static final int MULTIPLE = Choice.MULTIPLE;
    public static final int IMPLICIT = Choice.IMPLICIT;
    public List(String title, int listType) { }
    public List(String title, int listType, String[] stringElements,
            Image[] imageElements) { }
    public int size() { return 0; }
    public String getString(int elementNum) { return null; }
    public int append(String stringPart, Image imagePart) { return 0; }
    public void delete(int elementNum) { }
    public void deleteAll() { }
    public boolean isSelected(int elementNum) { return false; }
    public int getSelectedIndex() { return 0; }
    public void setSelectedIndex(int elementNum, boolean selected) { }
    public void setSelectCommand(Command c) { }
}
""")

tulis("javax.microedition.lcdui", "AlertType", """
public class AlertType {
    public static final AlertType INFO = new AlertType();
    public static final AlertType WARNING = new AlertType();
    public static final AlertType ERROR = new AlertType();
    public static final AlertType ALARM = new AlertType();
    public static final AlertType CONFIRMATION = new AlertType();
    protected AlertType() { }
    public boolean playSound(Display display) { return false; }
}
""")

tulis("javax.microedition.lcdui", "Alert", """
public class Alert extends Screen {
    public static final int FOREVER = -2;
    public Alert(String title) { }
    public Alert(String title, String alertText, Image alertImage,
            AlertType alertType) { }
    public void setTimeout(int time) { }
    public int getTimeout() { return 0; }
    public void setString(String str) { }
    public String getString() { return null; }
    public void setType(AlertType type) { }
}
""")

tulis("javax.microedition.lcdui", "Font", """
public final class Font {
    public static final int FACE_SYSTEM = 0;
    public static final int FACE_MONOSPACE = 32;
    public static final int FACE_PROPORTIONAL = 64;
    public static final int STYLE_PLAIN = 0;
    public static final int STYLE_BOLD = 1;
    public static final int STYLE_ITALIC = 2;
    public static final int STYLE_UNDERLINED = 4;
    public static final int SIZE_SMALL = 8;
    public static final int SIZE_MEDIUM = 0;
    public static final int SIZE_LARGE = 16;
    private Font() { }
    public static Font getDefaultFont() { return null; }
    public static Font getFont(int face, int style, int size) { return null; }
    public int getHeight() { return 12; }
    public int getBaselinePosition() { return 10; }
    public int charWidth(char ch) { return 6; }
    public int stringWidth(String str) { return str == null ? 0 : str.length() * 6; }
    public int substringWidth(String str, int offset, int len) { return len * 6; }
}
""")

tulis("javax.microedition.lcdui", "Image", """
public class Image {
    protected Image() { }
    public static Image createImage(int width, int height) { return new Image(); }
    public static Image createImage(String name) throws java.io.IOException {
        return new Image();
    }
    public static Image createImage(byte[] data, int off, int len) {
        return new Image();
    }
    public static Image createImage(Image source) { return new Image(); }
    public static Image createImage(Image image, int x, int y, int w, int h,
            int transform) { return new Image(); }
    public static Image createRGBImage(int[] rgb, int width, int height,
            boolean processAlpha) { return new Image(); }
    public Graphics getGraphics() { return null; }
    public int getWidth() { return 1; }
    public int getHeight() { return 1; }
    public boolean isMutable() { return false; }
    public void getRGB(int[] rgbData, int offset, int scanlength, int x, int y,
            int width, int height) { }
}
""")

tulis("javax.microedition.lcdui", "Graphics", """
public class Graphics {
    public static final int HCENTER = 1;
    public static final int VCENTER = 2;
    public static final int LEFT = 4;
    public static final int RIGHT = 8;
    public static final int TOP = 16;
    public static final int BOTTOM = 32;
    public static final int BASELINE = 64;
    public static final int SOLID = 0;
    public static final int DOTTED = 1;
    protected Graphics() { }
    public void setColor(int rgb) { }
    public void setColor(int r, int g, int b) { }
    public int getColor() { return 0; }
    public void setGrayScale(int value) { }
    public void setFont(Font font) { }
    public Font getFont() { return null; }
    public void setStrokeStyle(int style) { }
    public void setClip(int x, int y, int w, int h) { }
    public void clipRect(int x, int y, int w, int h) { }
    public int getClipX() { return 0; }
    public int getClipY() { return 0; }
    public int getClipWidth() { return 0; }
    public int getClipHeight() { return 0; }
    public void translate(int x, int y) { }
    public int getTranslateX() { return 0; }
    public int getTranslateY() { return 0; }
    public void drawLine(int x1, int y1, int x2, int y2) { }
    public void drawRect(int x, int y, int w, int h) { }
    public void fillRect(int x, int y, int w, int h) { }
    public void drawRoundRect(int x, int y, int w, int h, int aw, int ah) { }
    public void fillRoundRect(int x, int y, int w, int h, int aw, int ah) { }
    public void fillArc(int x, int y, int w, int h, int sa, int aa) { }
    public void drawArc(int x, int y, int w, int h, int sa, int aa) { }
    public void fillTriangle(int x1, int y1, int x2, int y2, int x3, int y3) { }
    public void drawString(String str, int x, int y, int anchor) { }
    public void drawSubstring(String str, int offset, int len, int x, int y,
            int anchor) { }
    public void drawChar(char character, int x, int y, int anchor) { }
    public void drawChars(char[] data, int offset, int length, int x, int y,
            int anchor) { }
    public void drawImage(Image img, int x, int y, int anchor) { }
    public void drawRegion(Image src, int xSrc, int ySrc, int width, int height,
            int transform, int xDest, int yDest, int anchor) { }
    public void copyArea(int xSrc, int ySrc, int width, int height, int xDest,
            int yDest, int anchor) { }
    public void drawRGB(int[] rgbData, int offset, int scanlength, int x, int y,
            int width, int height, boolean processAlpha) { }
}
""")

tulis("javax.microedition.lcdui", "Canvas", """
public abstract class Canvas extends Displayable {
    public static final int UP = 1;
    public static final int DOWN = 6;
    public static final int LEFT = 2;
    public static final int RIGHT = 5;
    public static final int FIRE = 8;
    public static final int GAME_A = 9;
    public static final int GAME_B = 10;
    public static final int GAME_C = 11;
    public static final int GAME_D = 12;
    public static final int KEY_NUM0 = 48;
    public static final int KEY_NUM1 = 49;
    public static final int KEY_NUM2 = 50;
    public static final int KEY_NUM3 = 51;
    public static final int KEY_NUM4 = 52;
    public static final int KEY_NUM5 = 53;
    public static final int KEY_NUM6 = 54;
    public static final int KEY_NUM7 = 55;
    public static final int KEY_NUM8 = 56;
    public static final int KEY_NUM9 = 57;
    public static final int KEY_STAR = 42;
    public static final int KEY_POUND = 35;
    protected Canvas() { }
    public int getGameAction(int keyCode) { return 0; }
    public int getKeyCode(int gameAction) { return 0; }
    public String getKeyName(int keyCode) { return null; }
    public boolean hasPointerEvents() { return false; }
    public boolean hasPointerMotionEvents() { return false; }
    public boolean hasRepeatEvents() { return false; }
    public boolean isDoubleBuffered() { return true; }
    public void setFullScreenMode(boolean mode) { }
    public void repaint() { }
    public void repaint(int x, int y, int width, int height) { }
    public void serviceRepaints() { }
    protected abstract void paint(Graphics g);
    protected void keyPressed(int keyCode) { }
    protected void keyReleased(int keyCode) { }
    protected void keyRepeated(int keyCode) { }
    protected void pointerPressed(int x, int y) { }
    protected void pointerReleased(int x, int y) { }
    protected void pointerDragged(int x, int y) { }
    protected void showNotify() { }
    protected void hideNotify() { }
}
""")

tulis("javax.microedition.lcdui.game", "GameCanvas", """
import javax.microedition.lcdui.Canvas;
import javax.microedition.lcdui.Graphics;

public abstract class GameCanvas extends Canvas {
    public static final int UP_PRESSED = 1 << Canvas.UP;
    public static final int DOWN_PRESSED = 1 << Canvas.DOWN;
    public static final int LEFT_PRESSED = 1 << Canvas.LEFT;
    public static final int RIGHT_PRESSED = 1 << Canvas.RIGHT;
    public static final int FIRE_PRESSED = 1 << Canvas.FIRE;
    public static final int GAME_A_PRESSED = 1 << Canvas.GAME_A;
    public static final int GAME_B_PRESSED = 1 << Canvas.GAME_B;
    public static final int GAME_C_PRESSED = 1 << Canvas.GAME_C;
    public static final int GAME_D_PRESSED = 1 << Canvas.GAME_D;
    protected GameCanvas(boolean suppressKeyEvents) { }
    protected Graphics getGraphics() { return null; }
    public int getKeyStates() { return 0; }
    public void paint(Graphics g) { }
    public void flushGraphics() { }
    public void flushGraphics(int x, int y, int width, int height) { }
}
""")

tulis("javax.microedition.lcdui.game", "Layer", """
import javax.microedition.lcdui.Graphics;

public abstract class Layer {
    Layer() { }
    public void setPosition(int x, int y) { }
    public void move(int dx, int dy) { }
    public final int getX() { return 0; }
    public final int getY() { return 0; }
    public final int getWidth() { return 0; }
    public final int getHeight() { return 0; }
    public void setVisible(boolean visible) { }
    public final boolean isVisible() { return true; }
    public abstract void paint(Graphics g);
}
""")

tulis("javax.microedition.lcdui.game", "Sprite", """
import javax.microedition.lcdui.Graphics;
import javax.microedition.lcdui.Image;

public class Sprite extends Layer {
    public static final int TRANS_NONE = 0;
    public static final int TRANS_ROT90 = 5;
    public static final int TRANS_ROT180 = 3;
    public static final int TRANS_ROT270 = 6;
    public static final int TRANS_MIRROR = 2;
    public static final int TRANS_MIRROR_ROT90 = 7;
    public static final int TRANS_MIRROR_ROT180 = 1;
    public static final int TRANS_MIRROR_ROT270 = 4;
    public Sprite(Image image) { }
    public Sprite(Image image, int frameWidth, int frameHeight) { }
    public void setFrame(int sequenceIndex) { }
    public int getFrame() { return 0; }
    public int getFrameSequenceLength() { return 0; }
    public void nextFrame() { }
    public void prevFrame() { }
    public void setTransform(int transform) { }
    public void defineReferencePixel(int x, int y) { }
    public void setRefPixelPosition(int x, int y) { }
    public boolean collidesWith(Sprite s, boolean pixelLevel) { return false; }
    public void paint(Graphics g) { }
}
""")

# ------------------------------------------------------------------- io
tulis("javax.microedition.io", "ConnectionNotFoundException", """
public class ConnectionNotFoundException extends java.io.IOException {
    public ConnectionNotFoundException() { }
    public ConnectionNotFoundException(String s) { super(s); }
}
""")

tulis("javax.microedition.io", "Connection", """
public interface Connection {
    void close() throws java.io.IOException;
}
""")

tulis("javax.microedition.io", "InputConnection", """
public interface InputConnection extends Connection {
    java.io.InputStream openInputStream() throws java.io.IOException;
    java.io.DataInputStream openDataInputStream() throws java.io.IOException;
}
""")

tulis("javax.microedition.io", "OutputConnection", """
public interface OutputConnection extends Connection {
    java.io.OutputStream openOutputStream() throws java.io.IOException;
    java.io.DataOutputStream openDataOutputStream() throws java.io.IOException;
}
""")

tulis("javax.microedition.io", "StreamConnection", """
public interface StreamConnection extends InputConnection, OutputConnection {
}
""")

tulis("javax.microedition.io", "SocketConnection", """
public interface SocketConnection extends StreamConnection {
    byte DELAY = 0;
    byte LINGER = 1;
    byte KEEPALIVE = 2;
    byte RCVBUF = 3;
    byte SNDBUF = 4;
    void setSocketOption(byte option, int value) throws java.io.IOException;
    int getSocketOption(byte option) throws java.io.IOException;
    String getLocalAddress() throws java.io.IOException;
    int getLocalPort() throws java.io.IOException;
    String getAddress() throws java.io.IOException;
    int getPort() throws java.io.IOException;
}
""")

tulis("javax.microedition.io", "HttpConnection", """
public interface HttpConnection extends StreamConnection {
    String GET = \"GET\";
    String POST = \"POST\";
    String HEAD = \"HEAD\";
    int HTTP_OK = 200;
    void setRequestMethod(String method) throws java.io.IOException;
    void setRequestProperty(String key, String value) throws java.io.IOException;
    int getResponseCode() throws java.io.IOException;
    long getLength();
}
""")

tulis("javax.microedition.io", "Connector", """
public class Connector {
    public static final int READ = 1;
    public static final int WRITE = 2;
    public static final int READ_WRITE = 3;
    private Connector() { }
    public static Connection open(String name) throws java.io.IOException {
        throw new ConnectionNotFoundException(\"stub\");
    }
    public static Connection open(String name, int mode)
            throws java.io.IOException {
        throw new ConnectionNotFoundException(\"stub\");
    }
    public static Connection open(String name, int mode, boolean timeouts)
            throws java.io.IOException {
        throw new ConnectionNotFoundException(\"stub\");
    }
    public static java.io.InputStream openInputStream(String name)
            throws java.io.IOException {
        throw new ConnectionNotFoundException(\"stub\");
    }
    public static java.io.OutputStream openOutputStream(String name)
            throws java.io.IOException {
        throw new ConnectionNotFoundException(\"stub\");
    }
}
""")

# ------------------------------------------------------------------ rms
for nama_kelas in ["RecordStoreException", "RecordStoreFullException",
                   "RecordStoreNotFoundException", "RecordStoreNotOpenException",
                   "InvalidRecordIDException"]:
    induk = "RecordStoreException"
    if nama_kelas == "RecordStoreException":
        induk = "Exception"
    tulis("javax.microedition.rms", nama_kelas, """
public class %s extends %s {
    public %s() { }
    public %s(String s) { super(s); }
}
""" % (nama_kelas, induk, nama_kelas, nama_kelas))

tulis("javax.microedition.rms", "RecordStore", """
public class RecordStore {
    private RecordStore() { }
    public static RecordStore openRecordStore(String name, boolean create)
            throws RecordStoreException { return new RecordStore(); }
    public static void deleteRecordStore(String name)
            throws RecordStoreException { }
    public static String[] listRecordStores() { return new String[0]; }
    public void closeRecordStore() throws RecordStoreException { }
    public int getNumRecords() throws RecordStoreException { return 0; }
    public int getSize() throws RecordStoreException { return 0; }
    public int getSizeAvailable() throws RecordStoreException { return 0; }
    public int addRecord(byte[] data, int offset, int numBytes)
            throws RecordStoreException { return 1; }
    public void setRecord(int recordId, byte[] newData, int offset,
            int numBytes) throws RecordStoreException { }
    public byte[] getRecord(int recordId) throws RecordStoreException {
        return null;
    }
    public void deleteRecord(int recordId) throws RecordStoreException { }
    public int getNextRecordID() throws RecordStoreException { return 1; }
}
""")


def main():
    jumlah = 0
    for (paket, nama), isi in FILE.items():
        folder = os.path.join(AKAR, *paket.split("."))
        os.makedirs(folder, exist_ok=True)
        jalur = os.path.join(folder, nama + ".java")
        isi_bersih = isi.strip("\n")
        if not isi_bersih.isascii():
            print("STUB_FAIL: karakter non-ascii di", jalur)
            return 1
        with open(jalur, "w", encoding="ascii") as f:
            f.write(CATATAN)
            f.write("package %s;\n\n" % paket)
            f.write(isi_bersih)
            f.write("\n")
        jumlah += 1
    print("stub  : %d file" % jumlah)
    print("folder: %s" % os.path.normpath(AKAR))
    print("STUB_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
