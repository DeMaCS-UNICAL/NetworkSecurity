import javax.net.ssl.SSLSocket;
import javax.net.ssl.SSLSocketFactory;
import java.io.*;

public class Client {

	public static void  main(String[] arstring) {
        try {
		SSLSocketFactory f = (SSLSocketFactory) SSLSocketFactory.getDefault();
		SSLSocket sslsocket =(SSLSocket) f.createSocket("localhost", 4433);

		InputStream inputstream = System.in;
		InputStreamReader inputstreamreader = new InputStreamReader(inputstream);
		BufferedReader bufferedreader = new BufferedReader(inputstreamreader);

		OutputStream outputstream = sslsocket.getOutputStream();
		OutputStreamWriter outputstreamwriter = new OutputStreamWriter(outputstream);
		BufferedWriter bufferedwriter = new BufferedWriter(outputstreamwriter);

		String string = null;
		while ((string = bufferedreader.readLine()) != null) {
			bufferedwriter.write(string + '\n');
			bufferedwriter.flush();
           	 }
        } catch (Exception exception) {
            exception.printStackTrace();
        }
    }
}




