import os
import sys
import numpy as np

class midi_reader:

    def __init__(self,wave_path):
        self.event_status = np.zeros((128,2))  # note status(0 is colsed,1 is open) event_index
        self.event_channel = []
        self.lastController = None
        with open(wave_path,"rb") as f:
            if f.read(8) != b"MThd\x00\x00\x00\x06":
                sys.stderr.write("no MThd head found\n")
                return None
            self.track_mode = int.from_bytes(f.read(2),byteorder="big") #0 单音轨 1 多音轨同步 2 多音轨不同步
            self.track_num = int.from_bytes(f.read(2),byteorder="big")
            self.tickPerQuarterNote = int.from_bytes(f.read(2),byteorder="big")
            for i in range(self.track_num):
                if f.read(4) != b"MTrk":
                    sys.stderr.write("why no MTrk found? track num is " + str(i) + "\n")
                    os._exit(0)
                byte_num = int.from_bytes(f.read(4),byteorder="big")
                # print(byte_num)
                self.last_type = None
                self.world_time = 0
                # print(byte_num)
                for j in range(byte_num):
                    #time
                    t = self.dynamic_byte(f)
                    # print("time:"+str(t))
                    self.world_time += t
                    #event
                    event_type = f.read(1)
                    if event_type == b"\xFF": #meta event
                        meta_type = f.read(1)
                        end_flag = self.parseMetaEvent(meta_type,f)
                        if end_flag:
                            break # track end

                    elif event_type == b"\xF0": #sys event
                        print("system event")
                        v_length = self.dynamic_byte(f)
                        text = f.read(v_length)

                    else:
                        self.parseMidiEvent(event_type,f)

    def __del__(self):
        pass

    def show_info(self):
        print(self.track_mode,self.track_num,self.tickPerQuarterNote)

    def parseMidiEvent(self,event_type,f):
        v_length = 0
        if b"\x80" <= event_type <= b"\x8F":
            print("note off")
            # byte1 = f.read(1)
            # byte2 = f.read(1)
            v_length = 2

        elif b"\x90" <= event_type <= b"\x9F": # note on velocity == 00 means note off
            note = int.from_bytes(f.read(1),byteorder="big")
            velocity = int.from_bytes(f.read(1),byteorder="big")
            if velocity == 0:
                # print("note off "+str(note))
                if self.event_status[note,0] != 1:
                    print("can not close a closed note")
                    os._exit(0)
                self.event_status[note,0] = 0
                # print("close "+str(note))
                eid = int(self.event_status[note,1])
                self.event_channel[eid].end_time = self.world_time
            else:
                # print("note on "+str(note))
                eid = len(self.event_channel)
                e = midi_event(start_time = self.world_time, program=self.program, note=note, velocity=velocity)
                if self.event_status[note,0] != 0:
                    print("can not open a opened note")
                    os._exit(0)
                self.event_status[note,0] = 1
                # print("open "+str(note))
                self.event_status[note,1] = eid
                self.event_channel.append(e)
            self.last_type = event_type

        elif b"\xA0" <= event_type <= b"\xAF":
            print("polyphonic after torch")
            # byte1 = f.read(1)
            # byte2 = f.read(1)
            v_length = 2

        elif b"\xB0" <= event_type <= b"\xBF":
            # print("control mode change")
            c_num = int.from_bytes(f.read(1),byteorder="big")
            c_value = int.from_bytes(f.read(1),byteorder="big")
            if self.lastController is not None:
                self.event_channel[self.lastController].end_time = self.world_time
            eid = len(self.event_channel)
            e = midi_event(start_time=self.world_time,end_time=self.world_time,program=self.program,controller=c_num,velocity=c_value)
            self.event_channel.append(e)
            self.last_type = event_type
            self.lastController = eid

        elif b"\xC0" <= event_type <= b"\xCF":
            # print(self.world_time)
            self.program = int.from_bytes(f.read(1),byteorder="big")
            # print("program change " + str(self.program))
            # v_length = 1

        elif b"\xD0" <= event_type <= b"\xDF":
            print("channel after torch")
            # byte1 = f.read(1)
            v_length = 1

        elif b"\xE0" <= event_type <= b"\xEF":
            print("pitch wheel range")
            # byte1 = f.read(1)
            # byte2 = f.read(1)
            v_length = 2

        elif b"\x00" <= event_type <=b"\x7F":
            # print("last type")
            self.parseLastEvent(f,event_type)
            # v_length = -1

        else :
            print("unknown event type")
            print(event_type)
            print(event_type.hex())
            os._exit(0)


    def parseLastEvent(self,f,byte1):
        if b"\x90" <= self.last_type <= b"\x9F":
            note = int.from_bytes(byte1,byteorder="big")
            velocity = int.from_bytes(f.read(1),byteorder="big")
            if velocity == 0:
                if self.event_status[note,0] != 1:
                    print("can not close a closed note")
                    os._exit(0)
                self.event_status[note,0] = 0
                # print("close "+str(note))
                eid = int(self.event_status[note,1])
                self.event_channel[eid].end_time = self.world_time
            else:
                eid = len(self.event_channel)
                e = midi_event(start_time = self.world_time, program=self.program, note=note, velocity=velocity)
                if self.event_status[note,0] != 0:
                    print("can not open a opened note")
                    os._exit(0)
                self.event_status[note,0] = 1
                # print("open "+str(note))
                self.event_status[note,1] = eid
                self.event_channel.append(e)

        elif b"\xB0" <= self.last_type <= b"\xBF":
            c_num = int.from_bytes(byte1,byteorder="big")
            c_value = int.from_bytes(f.read(1),byteorder="big")
            self.event_channel[self.lastController].end_time = self.world_time
            eid = len(self.event_channel)
            e = midi_event(start_time=self.world_time,end_time=self.world_time,program=self.program,controller=c_num,velocity=c_value)
            self.event_channel.append(e)
            self.lastController = eid

        else:
            print("unknown last type:")
            print(self.last_type)
            print(os._exit(0))

    def parseMetaEvent(self,meta_type,f):
        if meta_type == b"\x00":
            # print("设sequence num event")
            v_length = self.dynamic_byte(f)
            Sequence_number = f.read(v_length)
        elif meta_type == b"\x01":
            # print("Text event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        elif meta_type == b"\x02":
            print("copyright notice event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        elif meta_type == b"\x03":
            print("track name event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        elif meta_type == b"\x04":
            print("instrument name event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        elif meta_type == b"\x05":
            print("lyric name event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        elif meta_type == b"\x06":
            print("marker event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        elif meta_type == b"\x07":
            print("cue point event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        elif meta_type == b"\x2F":
            # print("track end event")
            byte00 = f.read(1)
            return True # track end
        elif meta_type == b"\x51":
            # print("tempo setting event")
            # print(self.world_time)
            v_length = self.dynamic_byte(f)
            time_per_quarter_note = int.from_bytes(f.read(v_length),byteorder="big")
            v_length = 0
            self.tick_time = time_per_quarter_note/self.tickPerQuarterNote   #us
            self.tempo = 60000000/time_per_quarter_note    #bpm
        elif meta_type == b"\x58":
            # print("time signature event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        elif meta_type == b"\x59":
            print("key signature event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        elif meta_type == b"\x7F":
            print("Sequencer specific event")
            v_length = self.dynamic_byte(f)
            text = f.read(v_length)
        else:
            print("unknown meta type")
            print(meta_type)
            os._exit(0)

        return False # track not end


    def dynamic_byte(self,f):
        array = []
        num = 0
        read_one = int.from_bytes(f.read(1),byteorder="big")
        while self.get_flag(read_one) == 1 :
            array.append(self.remove_flag(read_one))
            read_one = int.from_bytes(f.read(1),byteorder="big")
        array.append(read_one)

        length = len(array)
        for i in range(0,length):
            num += pow(128,length-1-i)*array[i]

        return num

    def normal(self):
        normal_tick_time = int(1/(self.tick_time/1000000))
        for event in self.event_channel:
            event.start_time /= normal_tick_time
            event.end_time /= normal_tick_time

    def get_flag(seflf,int_from_byte):
        return (int_from_byte >> 7)

    def remove_flag(self,int_from_byte):
        return (int_from_byte & 127)

    def get_events(self):
        return self.event_channel
        
class midi_event:
    def __init__(self,start_time,program,end_time=None,note=None,controller=None,velocity=None):
        self.start_time = start_time
        self.end_time = end_time
        self.program = program
        self.note = note
        self.controller = controller
        self.velocity = velocity    

        