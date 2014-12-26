import tkinter
import time
import threading
import random
import queue
import os
import sys
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename
import socket
class GuiPart:
    def __init__(self, master, queue,queue2,queue3,endCommand):
        self.first_click = True;
        self.prefix1='Server says:'#Add the prefix for good display
        self.prefix2='Client says:'
        #Cause tkinter is not safe in thread, So use queue 
        #The Python Queue class has been specifically designed to be thread-safe
        #in a multi-producer, multi-consumer environment. 
        self.queue1 = queue 
        self.queue2 = queue2
        self.queue3 = queue3
        # Set up the GUI
        master.wm_title("Chat Server")
        master.resizable('1','1')
        
        self.ui_messages = ScrolledText(
            master=master,
            wrap=tkinter.WORD,
            width=50,  # In chars
            height=25)  # In chars     

        self.ui_input = tkinter.Text(
            master=master,
            wrap=tkinter.WORD,
            width=50,
            height=4)
        
        # Bind the button-1 click of the Entry to the handler
        self.ui_input.bind('<Button-1>', self.eventInputClick)
        
        self.ui_button_send = tkinter.Button(
            master=master,
            text="Send",
            command=self.sendMsg)

        self.ui_button_file = tkinter.Button(
            master=master,
            text="File",
            command=self.sendFile)

        # Compute display position for all objects
        self.ui_messages.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.ui_input.pack(side=tkinter.TOP, fill=tkinter.BOTH)
        self.ui_button_send.pack(side=tkinter.LEFT)
        self.ui_button_file.pack(side=tkinter.RIGHT)
        # Add more GUI stuff here
        print("Starting serverUI...")
        self.ui_messages.insert(tkinter.END, "Adding a message to the text field...\n")
        self.ui_input.insert(tkinter.END, "<Enter message>")
       
    def processIncoming(self):
        """
        Handle all the messages currently in the queue (if any).
        """
        while self.queue1.qsize():
            try:
                msg = self.queue1.get(0)
                # Check contents of message and do what it says
                # As a test, we simply print it
                print (msg)
                self.ui_messages.insert(tkinter.INSERT, "%s\n" % (self.prefix2+msg))
                self.ui_messages.yview(tkinter.END)  # Auto-scrolling

            except Queue.Empty:
                pass
    # SEND button pressed
    def sendMsg(self):
        # Get user input (minus newline character at end)
        msg = self.ui_input.get("0.0", tkinter.END+"-1c")

        print("UI: Got text: '%s'" % msg)
        
        # Add this data to the message window
        if msg:
            self.ui_messages.insert(tkinter.INSERT, "%s\n" % (self.prefix1+msg))
            self.ui_messages.yview(tkinter.END)  # Auto-scrolling
            
            # Clean out input field for new data
            self.ui_input.delete("0.0", tkinter.END)
            self.registerEvent(self.queue2,msg)
            print("Test: Got text: '%s'" % msg)

    def registerEvent(self,container,msg):
        container.put(msg)


    # FILE button pressed
    def sendFile(self):
        file = askopenfilename()

        if(len(file) > 0 and os.path.isfile(file)):
            print("UI: Selected file: %s" % file)
        else:
            print("UI: File operation canceled")
        self.registerEvent(self.queue3,file)

        
    def eventInputClick(self, event):
        if(self.first_click):
            # If this is the first time the user clicked,
            # clear out the tutorial message currently in the box.
            # Otherwise, ignore it.
            self.ui_input.delete("0.0", tkinter.END)
            self.first_click = False;
    

class ThreadedServer:
    """
    Launch the main part of the GUI and the worker thread. periodicCall and
    endApplication could reside in the GUI part, but putting them here
    means that you have all the thread controls in a single place.
    """
    def __init__(self, master):
        """
        Start the GUI and the asynchronous threads. We are in the main
        (original) thread of the application, which will later be used by
        the GUI. We spawn a new thread for the worker.
        """
        self.master = master

        # Create the queues
        self.queue = queue.Queue()
        self.queue2 = queue.Queue()
        self.queue3 = queue.Queue() 
        # Set up the GUI part
        self.gui = GuiPart(master, self.queue,self.queue2,self.queue3,self.endApplication)
        self.conn_client()

        # Set up the thread to do asynchronous I/O
        # More can be made if necessary
        self.running = 1
        self.thread1 = threading.Thread(target=self.workerThread1)
        self.thread1.start()
        

        # Start the periodic call in the GUI to check if the queue contains
        # anything
        self.periodicCall()

        #This function differs itself from the Client in connecting with sever rather than listen
        #for request
    def conn_client(self):      
        port = 5000
         # Create TCP socket
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except socket.error as msg:
            print("Error: could not create socket")
            print("Description: " + str(msg))
            sys.exit()

        # Bind to listening port
        try:
            host=''  # Bind to all interfaces
            self.s.bind((host,port))
        except socket.error as msg:
            print("Error: unable to bind on port %d" % port)
            print("Description: " + str(msg))
            sys.exit()

        # Listen
        try:
            backlog=10  # Number of incoming connections that can wait
                        # to be accept()'ed before being turned away
            self.s.listen(backlog)
        except socket.error as msg:
            print("Error: unable to listen()")
            print("Description: " + str(msg))
            sys.exit()   

        print("Listening socket bound to port %d" % port)
         # Accept an incoming request
        try:
            (self.client_s, self.client_addr) = self.s.accept()
            # If successful, we now have TWO sockets
            #  (1) The original listening socket, still active
            #  (2) The new socket connected to the client
        except socket.error as msg:
            print("Error: unable to accept()")
            print("Description: " + str(msg))
            sys.exit()

        print("Accepted incoming connection from client")
        print("Client IP, Port = %s" % str(self.client_addr))
    #PeriodCall makes the most of the thread-safe interaction
    def periodicCall(self):
        """
        Check every 100 ms if there is something new in the queue.
        """
        self.gui.processIncoming()#call the gui thread to listen up to the data thread's action
        self.processIncoming()
        self.processFile()
        #call the data thread to listen up tp the gui thread's action
        
        if not self.running:
            # This is the brutal stop of the system. You may want to do
            # some cleanup before actually shutting it down.
            sys.exit(1)
        self.master.after(100, self.periodicCall)

    def workerThread1(self):
        """
        This is where we handle the asynchronous I/O. For example, it may be
        a 'select()'.
        """
        while self.running:
            # To simulate asynchronous I/O
            try:
                  buffer_size=4096
                  raw_bytes = self.client_s.recv(buffer_size)
            except socket.error as msg:
                 print("Error: unable to recv()")
                 print("Description: " + str(msg))
                 sys.exit()

            self.string = raw_bytes.decode()
            if not self.string:
                break
            print("Received %d bytes from client" % len(raw_bytes))
            print("Message contents: %s" % self.string)
            self.queue.put(self.string)


    def processIncoming(self):
        """
        Handle all the messages currently in the queue (if any).
        """

        while self.queue2.qsize():
            try:
                msg = self.queue2.get(0)
                # Check contents of message and do what it says
                # As a test, we simply print it
               
                self.client_s.sendall(msg.encode())
                print (msg)
                # self.ui_messages.insert(tkinter.INSERT, "%s\n" % (msg))
                # self.ui_messages.yview(tkinter.END)  # Auto-scrolling
            except Queue.Empty:
                pass

    def processFile(self):
        while self.queue3.qsize():
            try:
                filepath = self.queue3.get(0)
                # Check contents of message and do what it says
                # As a test, we simply print it
                print (filepath)
                try:
                    ff = open(filepath,'rb')
                    print ('Sending...')
                    ll = ff.read(1024)
                    while (ll):
                        print ('Sending...')
                        self.client_s.sendall(ll)
                        ll = ff.read(1024)
                    ff.close()
                    print ("Done Sending")
                except:
                    pass
            except Queue.Empty:
                pass
    def endApplication(self):
        self.running = 0
        self.gui.destroy()
        print("Stopping servertUI...")

root = tkinter.Tk()
client = ThreadedServer(root)
root.mainloop()