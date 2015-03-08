import os
import sys
import struct

TypeDescription = {
    0x0100: {
        'Text': 'with filenames',
        'Size': 18,
        'Format': '<14sI'
    },
    0x0200: {
        'Text': 'with numeric ids',
        'Size': 8,
        'Format': '<II'
    }
}


class BSARecord():
    def __init__(self, type, tuple, offset):
        self.type = type

        if self.type == 0x0100:
            self.filename = tuple[0].partition('\0')[0]
        else:
            self.filename = '%08d.DAT' % tuple[0]

        self.size = tuple[1]
        self.offset = offset
        self.data = None


class BSAFile():
    def __init__(self, filename):
        try:
            self.file = open(filename, 'rb')
        except:
            raise

        self.read_header()
        self.read_directory()


    def read_header(self):
        header = self.file.read(4)
        self.count, self.type = struct.unpack('HH', header)


    def read_directory(self):
        directory_size = self.count * TypeDescription[self.type]['Size']
        self.file.seek( -1 * directory_size, os.SEEK_END)
        string = self.file.read(directory_size)

        self.directory = { }

        offset = 4

        for i in range(0, self.count):
            rec = BSARecord(self.type, struct.unpack_from(
                    TypeDescription[self.type]['Format'], string,
                    i * TypeDescription[self.type]['Size']), offset)
            self.directory[rec.filename] = rec
            offset += rec.size

    def extract(self):
        for filename in self.directory:
            rec = self.directory[filename]
            self.file.seek(rec.offset)
            data = self.file.read(rec.size)
            print 'Extracting "%s" (%d bytes)...' % (filename, rec.size)
            fw = open(filename, 'wb')
            fw.write(data);
            fw.close()

    def get_record(self, filename):
        if filename not in self.directory:
            raise NotFound
    
        rec = self.directory[filename]

        self.file.seek(rec.offset)

        return self.file.read(rec.size)
        


