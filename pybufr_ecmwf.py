#!/usr/bin/env python

#  #[ documentation
# This module implements a python interface around the BUFR library provided by ECMWF
# to allow reading and writing the WMO BUFR file standard.
# For now, this is only a reference implementatio intended to demonstrate how
# this could be done.
#
# For more on information ECMWF see: http://www.ecmwf.int/
# For more information on the BUFR library software provided
# by ECMWF see: http://www.ecmwf.int/products/data/software/download/bufr.html
#
# Note about the use of the "#  #[" and "#  #]" comments:
#   these are folding marks for my favorite editor, emacs, combined with its folding mode
#   (see http://www.emacswiki.org/emacs/FoldingMode for more details)
# Please do not remove them.
#
# This module was written by: Jos de Kloe, KNMI, and may be redistributed for now
# under the terms of the GPL v.2.
#
# Modifications:
# J. de Kloe   12-Nov-2009    Initial version
#
#  #]
#  #[ imported modules
import os   # operating system functions
import sys  # system functions
import re   # regular expression handling
import glob # allow for filename expansion
import subprocess # support running additional executables
import shutil # portable file copying functions
#  #]

class bufr_interface:
    def __init__(self,verbose=False):
        self.verbose = verbose

class bufr_interface_ecmwf(bufr_interface):
    def __init__(self,verbose=False):
        #  #[

        # call the init of the parent class
        bufr_interface.__init__(self,verbose)
        # for now, this is equivalent to:
        #self.verbose = verbose

        self.ecmwf_bufr_lib_dir  = "./ecmwf_bufr_lib"

        # check for the presence of the library
        BufrLibFile = "libbufr.a"
        if (os.path.exists(BufrLibFile)):
            print "library seems present"
        else:
            print "Entering installation sequence:"
            self.__install__()

        self.wrapper_name = "ecmwfbufr.so"
        if (os.path.exists(self.wrapper_name)):
            print "python wrapper seems already present"
            return
        else:
            print "Entering wrapper generation sequence:"
            (Source_Dir,TarFile_to_Install) = self.__get_source_dir__()
            self.__generate_python_wrapper__(Source_Dir)

        #  #]
    def __download_library__(self):
        #  #[
        
        # this is the latest available version when I wrote this, dated 28-jul-2009
        #bufrlib_source_dir  = "http://www.ecmwf.int/products/data/software/download/software_files/"
        #bufrlib_source_file = "bufr_000380.tar.gz"
        url_bufr_page     = "http://www.ecmwf.int/products/data/software/download/bufr.html"
        url_ecmwf_website = "http://www.ecmwf.int/"

        os.makedirs(self.ecmwf_bufr_lib_dir)

        import urllib

        if (self.verbose):
            print "setting up connection to ECMWF website"
        try:
            # Get a file-like object for this website
            f = urllib.urlopen(url_bufr_page)
        except:
            print "connection failed......"
            print "could not open url: ",url_bufr_page
            sys.exit(1)

        # Read from the object, storing the page's contents in a list of lines
        lines = f.readlines()
        f.close()
        if (self.verbose):
            print "ECMWF download page retrieved successfully"
        
        # a test print of the html of this webpage
        #print "data:",s

        # do a simple parsing to retrieve the currently available BUFR library versions
        # and their URLs for download:

        # a little test to see how this regular expression grouping works:
        # (to be executed manually on the python prompt)
        # >import re
        # >x="abc 123 def 456 ghi"
        # >print re.match('.*(123).*(456).*',x).groups()
        # The output you get is:
        # ('123', '456')
        
        # the lines we are interested in have this format:
        # <TD WIDTH="37%"><A HREF="SOMEPATH/bufr_VERSION.tar.gz" class="sowtware">bufr_VERSION.tar.gz</A>DATE</TD>
        # so use this regular expression to parse these lines:
        LinePattern = r'<TD .*><A HREF="(.*)" .*>(.*)</A>(.*)</TD>'

        BufrLibVersions = []
        for l in lines:
            if (".tar.gz" in l):
                #print l
                MatchObject = re.match(LinePattern,l)
                if (MatchObject):
                    data = MatchObject.groups()
                    #print data
                    BufrLibVersions.append(data)

        # find most recent library version, for now just sort on name
        # that should do the trick
        MostRecentBufrLibURL       = ""
        MostRecentBufrTarFileName  = ""
        MostRecentBufrLibDate      = ""
        for data in BufrLibVersions:
            BufrLibURL      = data[0] # example: ('/products/data/software/download/software_files/bufr_000380.tar.gz'
            BufrTarFileName = data[1] # example: 'bufr_000380.tar.gz'
            BufrLibDate     = data[2] # example: ' 28.07.2009'
            if (BufrTarFileName > MostRecentBufrTarFileName):
                # store
                MostRecentBufrLibURL       = BufrLibURL
                MostRecentBufrTarFileName  = BufrTarFileName
                MostRecentBufrLibDate      = BufrLibDate

        # report the result
        if (self.verbose):
            print "Most recent library version seems to be: ",MostRecentBufrTarFileName
        download_url = url_ecmwf_website+MostRecentBufrLibURL

        if (self.verbose):
            print "trying to dowdload: ",MostRecentBufrTarFileName
        try:
            # Get a file-like object for this website
            f = urllib.urlopen(download_url)
        except:
            print "connection failed......"
            print "could not open url: ",download_url
            sys.exit(1)
        
        tarfiledata = f.read()
        f.close()
        if (self.verbose):
            print "ECMWF download page retrieved successfully"
        
        LocalFullName = os.path.join(self.ecmwf_bufr_lib_dir,MostRecentBufrTarFileName)
        fd = open(LocalFullName,'wb')
        fd.write(tarfiledata)
        fd.close()

        if (self.verbose):
            print "created local copy of: ",MostRecentBufrTarFileName
        #  #]
    def __get_source_dir__(self):
        #  #[
        list_of_bufrtarfiles = glob.glob(os.path.join(self.ecmwf_bufr_lib_dir,"*.tar.gz"))
        if (len(list_of_bufrtarfiles)==0):
            return None

        list_of_bufrtarfiles.sort(reverse=True)
        if (self.verbose):
            print "available library tarfiles: ",list_of_bufrtarfiles
            print "most recent library tarfile: ",list_of_bufrtarfiles[0]

        (path,TarFile_to_Install) = os.path.split(list_of_bufrtarfiles[0])
        (BUFR_Tar,ext1) = os.path.splitext(TarFile_to_Install)
        (BUFR_Dir,ext2) = os.path.splitext(BUFR_Tar)
        
        Source_Dir = os.path.join(self.ecmwf_bufr_lib_dir,BUFR_Dir)
        return (Source_Dir,TarFile_to_Install)
        #  #]
    def __install__(self):
        #  #[
        (Source_Dir,TarFile_to_Install) = self.__get_source_dir__()
        if (Source_Dir == None):
            self.__download_library__()
            # retry (hopefully we have a copy of the tarfile now)
            Source_Dir = self.__get_source_dir__()
            
        if (not os.path.exists(Source_Dir)):
            Cmd = "cd "+self.ecmwf_bufr_lib_dir+";tar zxvf "+TarFile_to_Install
            print "Executing command: ",Cmd
            os.system(Cmd)
        else:
            print "path exists: ",Source_Dir
            print "assuming the package is already unpacked..."

        # now use the Make command provided in this package

        #-----------------------------------------------------------------------------#
        # Possible commands to the make command for the BUFR library, in case you     #
        # wish to use the config files from the ECMWF software package are:           #
        # (see the README file within Source_Dir)                                     #
        # - architecture: ARCH=sgimips (or: decalpha,hppa,linux,rs6000,sun4)          #
        # - 64 bit machine: R64=R64                                                   #
        # - compiler name (only for linux or sun machines): CNAME=_gnu                #
        #                                                                             #
        #-----------------------------------------------------------------------------#

        # NOTE that for the linux case the library has some hardcoded switches to use
        # 32-bit variables in its interfacing, so DO NOT try to use the 64 bit option
        # on linux, even if you have a 64-bit processor and compiler available !
        # Even if the code runs, it will fail miserably and cause segmentation faults
        # if you are lucky, or just plain nonsense if you are out of luck ....

        # these 4 settings determine the name of the config file used by the Make command
        # look in ecmwf_bufr_lib/bufr_000380/config/ to see all available versions
        #ARCH="linux"
        #CNAME="_compiler"
        #R64="" 
        #A64=""
        
        # note: usefull free compilers for linux that you can use are:
        # g77      : CNAME="_gnu"
        # g95      : CNAME="_g95"
        # gfortran : CNAME="_gfortran"

        g77_present      = self.__CheckPresence__("g77")
        g95_present      = self.__CheckPresence__("g95")
        gfortran_present = self.__CheckPresence__("gfortran")
        f90_present      = self.__CheckPresence__("f90")
        f77_present      = self.__CheckPresence__("f77")

        gcc_present      = self.__CheckPresence__("gcc")
        cc_present       = self.__CheckPresence__("cc")

        if (self.verbose):
            print "f77_present      = ",f77_present
            print "f90_present      = ",f90_present
            print "g77_present      = ",g77_present
            print "g95_present      = ",g95_present
            print "gfortran_present = ",gfortran_present
            print "gcc_present      = ",gcc_present
            print "cc_present       = ",cc_present
            
        # Default compiler switches (e.g. for Portland/ifort).
        FFLAGS = "-O -Dlinux "
        CFLAGS = ""
        # force the BUFR library to use 4 byte integers as default
        FINTEGERDEFINITION=" -i4"
        CINTEGERDEFINITION=" -DFOPEN64 "

        # switch of (as test)
        g95_present = False

        if   (g95_present):
            FC = "g95"
            FFLAGS = FFLAGS+" -fno-second-underscore"
            FFLAGS = FFLAGS+" -r8"
            FFLAGS = FFLAGS+" -fPIC"
            CFLAGS = CFLAGS+" -fPIC"
            #CNAME="_g95"
        elif (gfortran_present):
            FC = "gfortran"
            FFLAGS = FFLAGS+" -fno-second-underscore"
            FFLAGS = FFLAGS+" -fPIC"
            CFLAGS = CFLAGS+" -fPIC"
            #FINTEGERDEFINITION=" -fdefault-integer-4"
            # an explicit 4-byte default integer options seems not to exists
            # for gfortran, so lets just hope that is the default ...
            FINTEGERDEFINITION=""
            #CNAME="_gfortran"
        elif (g77_present):
            FC = "g77"
            #CNAME="_gnu"
        elif (f90_present):
            # this catches installations that have some commercial fortran
            # installed, which usually are symlinked to the name
            # f90 for convenience
            FC = "f77"
            #CNAME="_???"
        elif (f77_present):
            # this catches installations that have some commercial fortran
            # installed, which usually are symlinked to the name
            # f77 for convenience
            FC = "f77"
            #CNAME="_???"
        else:
            print "ERROR in bufr_interface_ecmwf.__install__:"
            print "No suitable fortran compiler found"
            sys.exit(1)

        if   (gcc_present):
            CC="gcc"
        elif (cc_present):
            # this catches installations that have some commercial c-compiler
            # installed, which usually are symlinked to the name
            # cc for convenience
            CC="cc"
        else:
            print "ERROR in bufr_interface_ecmwf.__install__:"
            print "No suitable c compiler found"
            sys.exit(1)

        # no check implemented on the "ar" and "ranlib" commands yet
        # (easy to add if we woould need it)

        # a command to generate an archive (*.a) file
        AR="ar"
        # a command to generate an index of an archive file
        RL = "/usr/bin/ranlib"

        CFLAGS=CFLAGS+CINTEGERDEFINITION
        FFLAGS=FFLAGS+FINTEGERDEFINITION

        # Unfortunately, the config files supplied with this library seem
        # somewhat outdated and sometimes incorrect, or incompatible with
        # the current compiler version (since they seem based on some
        # older compiler version, used some time ago at ECMWF, and never
        # got updated). This especially is true for the g95 compiler.
        # Therefore we have decided (at KNMI) to create our own
        # custom config file in stead.
        # We just call it: config.linux_compiler
        # which seems safe for now, since ECMWF doesn't use that name.
        
        ARCH="linux"
        CNAME="_compiler"
        R64="" 
        A64=""

        # construct the name of the config file to be used
        ConfigFile = "config."+ARCH+CNAME+R64+A64
        FullnameConfigFile = os.path.join(Source_Dir,"config",ConfigFile)

        # this check is only usefull if you use one of the existing config files
        #if not os.path.exists(FullnameConfigFile):
        #    # see if a version with ".in" extension is present
        #    # and if so, symlink to it.
        #    if not os.path.exists(FullnameConfigFile+".in"):
        #        print "ERROR: config file not found: ",FullnameConfigFile
        #        sys.exit(1)
        #    else:
        #        os.symlink(ConfigFile+".in",FullnameConfigFile)

        # create our custom config file:
        print "Using: "+FC+" as fortran compiler"
        print "Using: "+CC+" as c compiler"
        fd = open(FullnameConfigFile,'wt')
        fd.write("#   Generic configuration file for linux.\n")
        fd.write("AR         = "+AR+"\n")
        fd.write("ARFLAGS    = rv\n")
        fd.write("CC         = "+CC+"\n")
        fd.write("CFLAGS     = -O "+CFLAGS+"\n")
        fd.write("FASTCFLAGS = "+CFLAGS+"\n")
        fd.write("FC         = "+FC+"\n")
        fd.write("FFLAGS     = "+FFLAGS+"\n")
        fd.write("VECTFFLAGS = "+FFLAGS+"\n")
        fd.write("RANLIB     = "+RL+"\n")
        fd.close()
        
        # construct the compilation command:
        Cmd = "cd "+Source_Dir+";make ARCH="+ARCH+" CNAME="+CNAME+" R64="+R64+" A64="+A64

        # now issue the Make command
        print "Executing command: ",Cmd
        os.system(Cmd)

        # check the result
        BufrLibFile = "libbufr.a"
        FullnameBufrLibFile = os.path.join(Source_Dir,BufrLibFile)
        if (os.path.exists(FullnameBufrLibFile)):
            print "Build seems successfull"
            # remove any old symlink that might be present
            if (os.path.exists(BufrLibFile)):
                os.remove(BufrLibFile)
            # make a symlink in a more convenient location
            os.symlink(FullnameBufrLibFile,BufrLibFile)
        else:
            print "ERROR in bufr_interface_ecmwf.__install__:"
            print "No libbufr.a file seems generated."
            sys.exit(1)
        #  #]
    def __CheckPresence__(self,command):
        #  #[
        if (self.verbose):
            print "checking for presence of command: "+command
        
        result = []
        
        # get the real command, in case it was an alias
        Cmd = "which "+command
        print "Executing command: ",Cmd
        SubPr = subprocess.Popen(Cmd,shell=True,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)

        # wait until the child process is done
        #SubPr.wait() # seems not necessary for our purpose

        lines_stdout = SubPr.stdout.readlines()
        lines_stderr = SubPr.stderr.readlines()
        
        #print "lines_stdout: ",lines_stdout
        #print "lines_stderr: ",lines_stderr

        if (len(lines_stdout)==0):
            # command is not present in default path
            return False
        else:
            # command is present in default path
            return True
        #  #]        
    def __generate_python_wrapper__(self,Source_Dir):
        #  #[
        wrapper_build_dir   = "f2py_build"
        wrapper_module_name = "ecmwfbufr"
        signatures_filename = "signatures.pyf"

        SrcFiles = ["buxdes.F",
                    "bufren.F",
                    "bufrex.F",
                    "btable.F",
                    "get_name_unit.F",
                    "bus012.F",
                    "busel.F",
                    "buprs0.F",
                    "buprs1.F",
                    "buprs2.F",
                    "buprs3.F",
                    "buukey.F",
                    "bupkey.F",
                    "buprq.F"]
        #SrcFileList = ' '.join(os.path.join(Source_Dir,"bufrdc",f) for f in SrcFiles)
        # compilation of the wrapper seems to work when I use
        # this selected set of fortran files, but when I try to import the module
        # in python I get the following error (don't know yet why):
        #   >>> import ecmwfbufr
        #   Traceback (most recent call last):
        #     File "<stdin>", line 1, in <module>
        #   ImportError: ./ecmwfbufr.so: undefined symbol: _gfortran_concat_string
        #   >>> 

        # just take them all
        SrcFileList = Source_Dir+"/bufrdc/*.F"

        # call f2py and create a signature file that defines the
        # interfacing to the fortran routines in this library
        Cmd = "f2py --build-dir "+wrapper_build_dir+\
              " -m "+wrapper_module_name+\
              " -h "+signatures_filename+\
              " "+SrcFileList
        print "Executing command: ",Cmd
        os.system(Cmd)

        # safety check: see if the signatures.pyf file really is created
        signatures_fullfilename = os.path.join(wrapper_build_dir,signatures_filename)
        if (not os.path.exists(signatures_fullfilename)):
            print "ERROR: build of python wrapper failed"
            print "the signatures file could not be found"
            sys.exit(1)

        # adapt the signature file
        # this is needed, since the wrapper generation fails to do a number
        # of file includes that are essential for the interface definition
        # To circumvent this, remove the not-properly defined constants
        # and replace them by their numerical values
        self.__adapt_f2py_signature_file__(signatures_fullfilename)

        Cmd = "f2py ./f2py_build/signatures.pyf -L./ -lbufr -c"
        print "Executing command: ",Cmd
        os.system(Cmd)

        # finally, again check for the presence of the wrapper
        # to see if the build was successfull
        if (os.path.exists(self.wrapper_name)):
            print "a python wrapper to the ECMWF BUFR library has been generated"
            return
        else:
            print "ERROR: build of python wrapper failed"
            print "the compilation or linking stage failed"
            sys.exit(1)

        #  #]
    def __adapt_f2py_signature_file__(self,signature_file):
        #  #[
        #signature_file = "f2py_build/signatures.pyf"

        # these values are defined in parameter.F 
        # PARAMETER(JSUP =   9,
        #          JSEC0=   3,
        #          JSEC1=  40,
        #          JSEC2=4096,
        #          JSEC3=   4
        #          JSEC4=   2,
        #          JELEM=320000,
        #          JSUBS=400,
        #          JCVAL=150 ,
        #          JBUFL=512000,
        #          JBPW =  32,
        #          JTAB =3000,
        #          JCTAB=3000,
        #          JCTST=9000,
        #          JCTEXT=9000,
        #          JWORK=4096000,
        #          JKEY=46,
        #          JTMAX=10,
        #          JTCLAS=64,
        #          JTEL=255)
        
        edits = {}
        edits['JSUP']  = 9
        edits['JSEC0'] = 3
        edits['JSEC1'] = 40
        edits['JSEC2'] = 4096
        edits['JSEC3'] = 4
        edits['JSEC4'] = 2
        edits['JELEM'] = 320000
        edits['JSUBS'] = 400
        edits['JCVAL'] = 150
        edits['JBUFL'] = 512000
        edits['JBPW'] = 32
        edits['JTAB'] = 3000
        edits['JCTAB'] = 3000
        edits['JCTST'] = 9000
        edits['JCTEXT'] = 9000
        edits['JWORK'] = 4096000
        edits['JKEY'] = 46
        edits['JTMAX'] = 10
        edits['JTCLAS'] = 64
        edits['JTEL'] = 255
        # edits[''] = 

        # read the file
        lines = open(signature_file).readlines()

        # create a backup copy, to allow manual inspection
        Source      = signature_file
        Destination = signature_file+".bak"
        shutil.copyfile(Source,Destination)
        
        fd = open(signature_file,"wt")
        for l in lines:
            if 'dimension' in l:
                #print "adapting line: ",l
                for e in edits.keys():
                    txt = '('+e.lower()+')'
                    value = edits[e]
                    if txt in l:
                        l=l.replace(txt,str(value))
                #print "to           : ",l
            fd.write(l)
        fd.close()
        #  #]

#  #[ some notes:
# manually, if I issue this command, it seems to work! this creates the file ./f2py_build/signatures.pyf
#   f2py --build-dir ./f2py_build -m ecmwfbufr -h signatures.pyf ecmwf_bufr_lib/bufr_000380/bufrdc/*.F

# afterwards I have to adapt the pyf file with my little adapt_signature_file.py script
# Then for gfortran the following command works fine:
#   f2py ./f2py_build/signatures.pyf -L./ -lbufr -c
# now indeed the wrapper shared object file ecmwfbufr.so has been generated.

# Note that on my home machine I have to use:
#   setenv LD_LIBRARY_PATH /home/jos/bin/gcc-trunk/lib64/
# since I have gfortran installed in a non-default location
# (otherwise the linking step needed to create the *.so file fails)
#  #]

class bufrmsg:
    pass

class bufrfile:
    pass


if __name__ == "__main__":
        #  #[ test program
        print "Starting test program:"

        # instantiate the class, and pass all settings to it
        BI = bufr_interface_ecmwf(verbose=True)
        
        #  #]
