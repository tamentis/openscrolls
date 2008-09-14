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



class BSAFile():
    def __init__(self, filename):
        try:
            self.file = open(filename, 'r')
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

        self.directory = [ ]

        for i in range(0, self.count):
            rec = struct.unpack_from(TypeDescription[self.type]['Format'], string,
                i * TypeDescription[self.type]['Size'])
            self.directory.append(rec)

    def extract(self):
        self.file.seek(4)

        for rec in self.directory:
            data = self.file.read(rec[1])
            if self.type == 0x0100:
                filename = rec[0].partition('\0')[0]
            else:
                filename = '%08d.DAT' % rec[0]
            print 'Extracting "%s" (%d bytes)...' % (filename, rec[1])
            fw = open(filename, 'w')
            fw.write(data);
            fw.close()


if '-h' in sys.argv or len(sys.argv) != 2:
    print """
     Usage: openscrolls_unbsa <file>

     Extracts all the records within a BSA file.
    """
    exit()


bsa = BSAFile(sys.argv[1])


print 'This BSA file holds %d records of type %x (%s).' % ( bsa.count, bsa.type,
        TypeDescription[bsa.type]['Text'])

bsa.extract()


