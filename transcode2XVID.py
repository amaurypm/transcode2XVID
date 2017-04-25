#!/usr/bin/env python2
# -*- coding: utf-8 -*-
## A wrapper script to transcode video files to XviD, MP3 in AVI format, using
## avconv and mkvmerge.
##
## Amaury Pupo Merino
## amaury.pupo@gmail.com
## February 2013
## Modified in January 2017, to include hard sub and be ported to ffmpeg.
##
## This small piece of code is released under GPL v3.
##

## Importing modules
import sys
import os
import optparse
import time
import random
import shutil

## Classes
class Video:
    """Contains actual and proposed video information, and can transforme itself.
    
    """
    def __init__(self,filename):
        self.__in_filename=filename       
        self.__in_ok=False
        self.__in_duration=None
        self.__in_width=None
        self.__in_height=None
        self.__get_input_data()
        self.__quantizer=None
        self.__sub_file=None
        self.__sub_exts=['.srt','.ass','.ssa','.txt']
        self.__hardsub=None
        #self.__sub_charsets = {}
        self.__out_postfix=None
        self.__out_ext='.avi'        
        self.__replace_original=False        
        self.__crop_data=None
        self.__out_MAX_WIDTH=720

    def __get_input_data(self):
        if os.path.isfile(self.__in_filename):
            cmd_in_file,cmd_output_error_file=os.popen4("ffmpeg -i \"%s\"" % self.__in_filename)
            for line in cmd_output_error_file:            
                line=line.strip()
                if ('Video' in line) and ('Stream' in line):
                    self.__in_ok=True
                    wh_info = line.split(',')[2].strip().split()[0]
                    if 'x' not in wh_info:
						wh_info = line.split(',')[3].strip().split()[0]						
                    
                    try:
						self.__in_width,self.__in_height=wh_info.split('x')
						self.__in_width,self.__in_height=int(self.__in_width),int(self.__in_height)
                        
                    except:
                        sys.stderr.write('WARNING: Input video dimensions can not be extracted.\n')
                    
                if 'Duration' in line:
                    duration_string=line.split(',')[0].split()[1]
                    if not 'N/A' in duration_string:
                        self.__in_duration=dstring2dint(duration_string)
                        
    def is_ok(self):
        """Returns true is video file exist and it is actually a video.
        
        """
        return self.__in_ok
    

    def __find_ext_subtitle(self):
        if self.__in_ok:
            subtitle_filename_root=os.path.splitext(self.__in_filename)[0]
            for subtitle_extension in self.__sub_exts:
                subtitle_filename=subtitle_filename_root+subtitle_extension
                if os.path.isfile(subtitle_filename):
                    self.__sub_file=subtitle_filename
                    #self.__find_sub_charset(subtitle_filename)
                    return

    def __try_to_convert_sub_to_srt(self):
        subtitle_filename_root,subtitle_filename_ext=os.path.splitext(self.__sub_file)
        if subtitle_filename_ext == '.srt':
            return
        
        tmp_filename=self.__sub_file
        
        self.__sub_file=ass2srt(self.__sub_file)
        
                    
    def set_transcoding_options(self,quantizer,replace_original,postfix,auto_crop, hardsub):
        if self.__in_ok:
            self.__quantizer=quantizer
            self.__find_ext_subtitle()
            if not self.__sub_file:
                self.__find_int_subtitle()

            self.__replace_original=replace_original
            self.__out_postfix=postfix
            if auto_crop:
                sys.stdout.write('Finding crop dimensions...')
                sys.stdout.flush()
                self.__get_crop_data()
                
            self.__hardsub = hardsub
                
            self.__transcoding_options_set=True
            
    def __find_int_subtitle(self):
        if not self.__sub_file:
            in_filename_root,in_filename_ext=os.path.splitext(self.__in_filename)
            if in_filename_ext == '.mkv':
                for line in os.popen("mkvmerge -i \"%s\"" % self.__in_filename):
                    if 'subtitles' in line:
                        track_id=int(line.strip().split(":")[0].split()[2])
                        sub_type=line.strip().split('/')[1].strip(")")
                        sub_ext='.srt'
                        if sub_type in ['ASS','SSA']:
                            sub_ext='.ass'
                            
                        os.system("mkvextract tracks \"%s\" %d:\"%s\"" % (self.__in_filename, track_id, in_filename_root+sub_ext))
                        self.__sub_file=in_filename_root+sub_ext
                        #self.__find_sub_charset(self.__sub_file)
                        
    #def __find_sub_charset(self, filename):
    #    cmd_output=os.popen("file -bi \"{}\" | sed -e 's/.*charset=//'".format(filename))
    #    for line in cmd_output:
    #        line=line.strip()
    #        if line:
    #            self.__sub_charsets[filename]=line
                        
    def transcode(self):
        if self.__transcoding_options_set:
            #cmd_line='ffmpeg -i \"%s\" -vcodec libxvid -q:v %d' % (self.__in_filename, self.__quantizer)
            cmd_line='ffmpeg -i \"%s\"' % self.__in_filename
            
            #if self.__hardsub:
			#	if self.__sub_charsets and (self.__sub_file in self.__sub_charsets):
			#				cmd_line += ' -sub_charenc %s' %  self.__sub_charsets[self.__sub_file]
							
            cmd_line += ' -vcodec libxvid -q:v %d' % self.__quantizer  
				
            aspect=self.__calc_out_aspect()
            
            if aspect:
                cmd_line+=' -aspect %s' % aspect
                
            if self.__crop_data or (self.__in_width > self.__out_MAX_WIDTH) or (self.__hardsub and self.__sub_file):
                cmd_line+=' -vf '  
                
            if self.__crop_data:
                cmd_line+=' crop=%s' % self.__crop_data
                    
            if self.__in_width > self.__out_MAX_WIDTH:
                if self.__crop_data:
                    cmd_line+=','
                    
                if aspect:
                    cmd_line+='scale=%s' % aspect
                    
                else:
                    cmd_line+='scale=%d:-1' % self.__out_MAX_WIDTH             
            
            
            if self.__hardsub and self.__sub_file:
				if ('crop' in cmd_line) or ('scale' in cmd_line):
					cmd_line += ','
					
				sub_ext = os.path.splitext(self.__sub_file)[1]
				if sub_ext.lower() in (".srt",".txt"):
					cmd_line += 'subtitles=%s' % self.__sub_file					
					
				elif sub_ext.lower() in (".ass",".ssa"):
					cmd_line += '"ass=%s"' % self.__sub_file	
                
            			
				                  
                
            cmd_line+=' -acodec libmp3lame -ar 48k -aq 2 -sn -y \"%s\"' % (os.path.splitext(self.__in_filename)[0]+self.__out_postfix+self.__out_ext)
            sys.stdout.write('> %s\n' % cmd_line)
            exit_code=os.system(cmd_line)
            
            if not exit_code:
				if not self.__hardsub:
					self.__copy_subtitle()
					                             
				if self.__replace_original:
					sys.stderr.write("WARNING: Deleting file %s as commanded with -r option.\nThis file won't be easily recovered.\n" % self.__in_filename)
					os.remove(self.__in_filename)
					
				return True
        
        return False
    
    def __copy_subtitle(self):
        if self.__sub_file:
            sub_file_root,sub_file_ext=os.path.splitext(self.__sub_file)
            out_sub_filename=sub_file_root+self.__out_postfix+sub_file_ext
            shutil.copyfile(self.__sub_file,out_sub_filename)
            
    def __calc_out_aspect(self):
        aspect=None
        if self.__in_width > self.__out_MAX_WIDTH:
            out_width=self.__out_MAX_WIDTH
            out_height=self.__in_height*out_width/self.__in_width
            
        elif self.__crop_data:
            out_width,out_height=int(self.__crop_data.split(':')[0]),int(self.__crop_data.split(':')[1])
            
        else:
            out_width,out_height=self.__in_width,self.__in_height
            
        while out_width%8:
            out_width-=1
            
        while out_height%8:
            out_height-=1            
                
        aspect='%d:%d' % (out_width,out_height)
        return aspect
    
       
    def __get_crop_data(self):
        crop_data=None
        crop_list=[]
        tmp_output_filename=os.path.splitext(self.__in_filename)[0]+'_tmp_transcode2XVID-autocrop.mkv'
        input_duration=self.__in_duration
        if input_duration:
            ss_list=[input_duration/x for x in random.sample(range(1,100),5)] # Cheacking autocrop in 5 random sites in the video.
            for ss in ss_list:
                cmd_in_file,cmd_output_error_file=os.popen4("ffmpeg -ss %d -i \"%s\" -t 1 -filter cropdetect -y \"%s\"" % (ss,self.__in_filename,tmp_output_filename))
                for line in cmd_output_error_file:
                    line=line.strip()
                    if ('cropdetect' in line) and ('=' in line):
                        crop_list.append(line.split('=')[1])
                        
            os.remove(tmp_output_filename)            
            crop_set=set(crop_list)
            crop_mode_cont=0
            for crop in crop_set:
                if crop_list.count(crop) > crop_mode_cont:
                    crop_data=crop
                    crop_mode_cont=crop_list.count(crop)
            
        sys.stdout.write('%s\n' % crop_data)
        self.__crop_data=crop_data
    
class Reporter:
    """Holds information about the transcoding process and elaborate a final report.
    
    """
    def __init__(self):
        self.__files_ok_counter=0
        self.__files_with_error=[]
        self.__ignored_files=[]
        
    def count_file_ok(self):
        self.__files_ok_counter+=1
        
    def add_file_with_errors(self,filename):
        self.__files_with_error.append(filename)
        
    def add_ignored_file(self,filename):
        self.__ignored_files.append(filename)
        
    def print_final_report(self):
        """Print report after all transcoding is made.
        """
        print('\n==== Transcoding finished ====')
        if self.__ignored_files:
            print ('== There following files were ignored: ==')
            for filename in self.__ignored_files:
                print('\t* %s' % filename)
                
            print(75*'=')
            print('\n')
            
        if self.__files_with_error:
            print ('== There were errors transcoding the files: ==')
            for filename in self.__files_with_error:
                print('\t* %s' % filename)
                
            print(75*'=')
            print('\n')
            
        print('==== Final report ====')
        output='\t %d file' % self.__files_ok_counter
        if self.__files_ok_counter!=1:
            output+='s'
            
        output+=' transcoded OK.\n'
        output+='\t %d file' % len(self.__files_with_error)
                    
        if len(self.__files_with_error)!=1:
            output+='s'
            
        output+=' with errors.\n'
        
        sys.stdout.write(output)
            
        print(75*'=')
        print('\n')

## Functions
def check_the_required_programs():
    if os.system("ffmpeg -h > /dev/null 2>&1"):
        sys.stderr.write("ERROR: ffmpeg is not installed in your system.\nThis script can not work properly without it.\nIf you are using Ubuntu just type:\n\tsudo apt-get install libav-tools\n\n")
        exit()
        
    if os.system("mkvmerge -h > /dev/null"):
        sys.stderr.write("ERROR: mkvtoolnix is not installed in your system.\nThis script can not work properly without it.\nIf you are using Ubuntu just type:\n\tsudo apt-get install mkvtoolnix\n\n")
        exit()
        
def print_duration(seconds):
    output=''
    seconds_per_minute=60
    seconds_per_hour=60*seconds_per_minute
    seconds_per_day=24*seconds_per_hour
    
    days=int(seconds/seconds_per_day)
    hours=int((seconds % seconds_per_day)/seconds_per_hour)
    minutes=int((seconds % seconds_per_hour)/seconds_per_minute)
    seconds=seconds%60
    
    if days:
        output+=('%d' % (days))
        if days==1:
            output+=' day '
            
        else:
            output+=' days '
            
    if hours:
        output+=('%2d' % (hours))
        if hours==1:
            output+=' hour '
            
        else:
            output+=' hours '
            
    if minutes:
        output+=('%2d' % (minutes))
        if minutes==1:
            output+=' minute '
            
        else:
            output+=' minutes '
            
    if seconds:
        output+=('%4.2f' % (seconds))
        if seconds==1:
            output+=' second '
            
        else:
            output+=' seconds '
                
    return output.strip()

    
def ass2srt(in_filename):
    out_filename=os.path.splitext(in_filename)[0]+'.srt'
    in_file=open(in_filename,'r')
    out_file=open(out_filename,'w')
    dialog_counter=0
    for line in in_file:
        dialog=''
        line=line.strip()
        if line[:9] == 'Dialogue:':
            dialog_counter+=1
            fields=line[10:].split(',')
            ftime=line[10:].split(',')[1]
            ltime=line[10:].split(',')[2]
            for sentence in fields[3:]:
                dialog+=(sentence+',')
                
            dialog=dialog.rstrip(',')
            ftime_hour,ftime_min,ftime_seconds=ftime.split(':')
            ftime_hour,ftime_min=int(ftime_hour),int(ftime_min)
            ftime_seconds,ftime_mseconds=ftime_seconds.split('.')
            ftime_seconds,ftime_mseconds=int(ftime_seconds),int(ftime_mseconds)*10

            ltime_hour,ltime_min,ltime_seconds=ltime.split(':')
            ltime_hour,ltime_min=int(ltime_hour),int(ltime_min)
            ltime_seconds,ltime_mseconds=ltime_seconds.split('.')
            ltime_seconds,ltime_mseconds=int(ltime_seconds),int(ltime_mseconds)*10
            
            output_line="%d\n%02d:%02d:%02d,%03d --> %02d:%02d:%02d,%03d\n%s\n\n" % (dialog_counter,ftime_hour,ftime_min,ftime_seconds,ftime_mseconds,ltime_hour,ltime_min,ltime_seconds,ltime_mseconds,dialog)
            out_file.write(output_line)
            
    
    in_file.close()
    out_file.close()
    
    return out_filename

def dstring2dint(duration_string):
    hours,minutes,seconds=duration_string.split(':')
    hours,minutes,seconds=int(hours),int(minutes),int(round(float(seconds)))
    duration_seconds=3600*hours+60*minutes+seconds
    return duration_seconds

def run_script():
    """Function to be called to actually run the script.
    """
    check_the_required_programs()
    initial_time=time.time()
    usage="%prog [options] video_file[s]"
    description="This program transcode video files to XviD and MP3 in an AVI format. Output files are optimized for DVD players, but compatible with devices supporting DivX/Xvid. Subtitles are handled automatically and, if present, subtitle files with compatible names will be created for output files or it can be hardsubbed if the appropriate option is selected."
    version='%prog 2.3.0'
    parser=optparse.OptionParser(usage=usage,description=description,version=version)
    parser.add_option('-q','--quantizer',type=int,default=4,help='Quantizer value [default: %default]. Determines the output video quality. Smaller values gives better qualities and bigger file sizes, bigger values result in less quality and smaller file sizes. Default value results in a nice quality/size ratio. Quantizer values should be in the range of 2 to 31.')
    parser.add_option('-r','--replace-original-video-file',action='store_true',default=False,dest='replace',help='If True original video files will be erased after transcoding [default: %default]. WARNING: deleted files can not be easily recovered!')
    parser.add_option('-x','--filename-postfix',default='_xvid',help='Postfix to be added to newly created XviD video files [default: %default].')
    parser.add_option('-c','--auto-crop',action='store_true',default=False,help='Autocrop output files [default: %default]. WARNING: Use with caution as some video files has variable width horizontal (and vertical) black bars, in those cases you will probably lose data.')
    parser.add_option('-s','--hardsub',action='store_true',default=False,help='If True then the corresponding subtitles will be hardsubbed to videos [default: %default].')    
    
    (options,args)=parser.parse_args()
        
    if not len(args):
        parser.error('You need to specify at least one video file.\nSee help (-h, --help) for more options.')
        
    if options.quantizer < 2 or options.quantizer > 31:
        parser.error('Quantizer values should be in the range of 2 to 31.')

    reporter=Reporter()
    file_counter=0
    for filename in args:
        file_counter+=1        
        print('\n==== Transcoding file %d/%d ====' % (file_counter,len(args)))
        video=Video(filename)
        if not video.is_ok():
            sys.stderr.write("File %s is not a proper video file.\n" % filename)
            reporter.add_ignored_file(filename)
            continue
        
        video.set_transcoding_options(options.quantizer,options.replace,options.filename_postfix,options.auto_crop, options.hardsub)
        if video.transcode():
            reporter.count_file_ok()
            
        else:
            reporter.add_file_with_errors(filename)
            
        print(75*'=')
            
    reporter.print_final_report()
        
    final_time=time.time()
    print 'Work finished in %s.' % print_duration(final_time-initial_time)
    print 'Exiting OK.'
    
## Running the script
if __name__ == "__main__":
    run_script()
