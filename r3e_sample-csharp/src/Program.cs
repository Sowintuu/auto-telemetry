using System;
using System.Diagnostics;
using System.IO;
using System.IO.MemoryMappedFiles;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Forms;
using System.Net;
using System.Net.Sockets;
using System.Text;
using R3E.Data;

namespace R3E
{
    class Sample : IDisposable
    {
        private bool Mapped 
        {
            get { return (_file != null); }
        }

        private Shared _data;
        private MemoryMappedFile _file;
        private byte[] _buffer;

        private readonly TimeSpan _timeAlive = TimeSpan.FromMinutes(9999);
        private readonly TimeSpan _timeInterval = TimeSpan.FromMilliseconds(100);

        public void Dispose()
        {
            _file.Dispose();
        }

        public void Run()
        {   
            // init timing.
            var timeReset = DateTime.UtcNow;
            var timeLast = timeReset;

            // Init socket.
            UdpClient udpClient = ConnectUdp();

            // Start data loop, connecting to sim.
            Console.WriteLine("Looking for RRRE.exe...");

            while(true)
            {
                var timeNow = DateTime.UtcNow;

                if(timeNow.Subtract(timeReset) > _timeAlive)
                {
                    break;
                }

                if(timeNow.Subtract(timeLast) < _timeInterval)
                {
                    Thread.Sleep(1);
                    continue;
                }

                timeLast = timeNow;

                if(Utilities.IsRrreRunning() && !Mapped)
                {
                    Console.WriteLine("Found RRRE.exe, mapping shared memory...");

                    if(Map())
                    {
                        Console.WriteLine("Memory mapped successfully");
                        timeReset = DateTime.UtcNow;

                        _buffer = new Byte[Marshal.SizeOf(typeof(Shared))];
                    }
                }

                if(Mapped)
                {
                    //Print();
                    Send(udpClient);
                }
            }

            Console.WriteLine("All done!");
        }

        private UdpClient ConnectUdp()
        {
            UdpClient client = new UdpClient(11000);
            try
            {
                client.Connect("localhost", 11000);
            }
            catch (Exception e)
            {
                Console.WriteLine(e.ToString());
                return null;
            }

            Console.WriteLine("UDP connected.");

            return client;
        }


        private bool Map()
        {
            try
            {
                _file = MemoryMappedFile.OpenExisting(Constant.SharedMemoryName);
                return true;
            }
            catch(FileNotFoundException)
            {
                return false;
            }
        }

        private bool Read()
        {
            try
            {
                var _view = _file.CreateViewStream();
                BinaryReader _stream = new BinaryReader(_view);
                _buffer = _stream.ReadBytes(Marshal.SizeOf(typeof(Shared)));
                GCHandle _handle = GCHandle.Alloc(_buffer, GCHandleType.Pinned);
                _data = (Shared)Marshal.PtrToStructure(_handle.AddrOfPinnedObject(), typeof(Shared));
                _handle.Free();

                return true;
            }
            catch(Exception)
            {
                return false;
            }
        }

        private void Print()
        {
            if (Read())
            {
                Console.WriteLine("Name: {0}", System.Text.Encoding.UTF8.GetString(_data.PlayerName).TrimEnd('\0'));

                if (_data.Gear >= -1)
                {
                    Console.WriteLine("Gear: {0}", _data.Gear);
                }

                if (_data.EngineRps > -1.0f)
                {
                    Console.WriteLine("RPM: {0}", Utilities.RpsToRpm(_data.EngineRps));
                    Console.WriteLine("Speed: {0}", Utilities.MpsToKph(_data.CarSpeed));
                }


                Console.WriteLine("");
            }
        }

        private void Send(UdpClient client)
        {
            string sendString = "";

            // Get data from buffer.
            if (Read())
            {
                // Gather data to send string.
                // Time stamp.
                sendString += $"Ti:{_data.Player.GameSimulationTime};";

                // Car location.
                sendString += $"Lx:{_data.CarCgLocation.X};";
                sendString += $"Ly:{_data.CarCgLocation.Y};";
                sendString += $"Lz:{_data.CarCgLocation.Z};";

                // Car speed.
                sendString += $"S:{Utilities.MpsToKph(_data.CarSpeed)};";

                // Car acceleration.
                sendString += $"Ax:{_data.LocalAcceleration.X};";
                sendString += $"Ay:{_data.LocalAcceleration.Y};";
                sendString += $"Az:{_data.LocalAcceleration.Z};";

                // RPM
                sendString += $"R:{Utilities.RpsToRpm(_data.EngineRps)};";

                // Gear.
                sendString += $"G:{_data.Gear};";

                //Throttle.
                sendString += $"T:{_data.Throttle};";

                //Brake.
                sendString += $"B:{_data.Throttle};";

                // Steering.
                sendString += $"St:{_data.SteerInputRaw};";

                // Prepare and send the string.
                // Trim trailing semicolon.
                sendString = sendString.TrimEnd(';');

                // Print for debug.
                Console.WriteLine(sendString);

                // Convert to byte array.
                Byte[] sendBytes = Encoding.ASCII.GetBytes(sendString);

                // Send the string.
                client.Send(sendBytes, sendBytes.Length);
            }


        }


    }

    class Program
    {
        static void MainSafe(string[] args)
        {
            using(var sample = new Sample())
            {
                sample.Run();
            }
        }

        static void Main(string[] args)
        {
            if(Debugger.IsAttached)
            {
                MainSafe(args);
            }
            else
            {
                try
                {
                    MainSafe(args);
                }
                catch (Exception e)
                {
                    MessageBox.Show(e.ToString());
                }
            }
        }
    }
}
