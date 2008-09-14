{$A+,B-,D+,E-,F-,G+,I-,L+,N-,O-,P+,Q-,R-,S-,T+,V-,X+,Y+}
{$M 4096,0,262144}
program hmi2mid;

{ Copyright (C) 1999 by Josef Drexler <jdrexler@uwo.ca>
  May be distributed under the terms of the GNU General
  Public License, version 2 or higher. }

uses
  dos;

{ $DEFINE DEBUG}

const
  blocksize = 65520;
  maxtracks = 64;

{ Filemodes for Reset }
const
  OF_READ               = $0000;
  OF_WRITE              = $0001;
  OF_READWRITE          = $0002;
  OF_SHARE_COMPAT       = $0000;
  OF_SHARE_EXCLUSIVE    = $0010;
  OF_SHARE_DENY_WRITE   = $0020;
  OF_SHARE_DENY_READ    = $0030;
  OF_SHARE_DENY_NONE    = $0040;
type
  thangingnotes = array[1..65535 div 4, 1..4] of byte;
  phangingnotes = ^thangingnotes;
  tlongarray = array[1..65535 div 4] of longint;
  plongarray = ^tlongarray;

var
  fin,
  fout : file;

  inbuf,
  outbuf : pchar;

  finpos,
  inblock,
  inrest,
  size,
  skipped : longint;

  inpos,
  outpos : word;

const
  lastkey : char = #13;
function extreadkey : char;
const
  oldscan : char = #0;
  isold : boolean = false;
begin
  if isold then
    begin
      extreadkey := oldscan;
      isold := false;
    end
  else
    asm
      mov ah,10h
      int 16h
      mov @result,al
      or al,al
      je @extended
      cmp al,0e0h
      jne @ok
      mov @result,0
@extended:
      mov isold,true
      mov oldscan,ah
@ok:
    end;
  asm
    mov al,@result
    mov lastkey,al
  end;
end;
const
  allnibbles : boolean = true;
var
  wasnonzero : boolean;
function hexnibble(b : byte) : string;
const
  hexchars : array[0..15] of char
	   = '0123456789ABCDEF';
begin
  if allnibbles or wasnonzero or (b <> 0) then
    begin
      hexnibble := hexchars[b];
      wasnonzero := true;
    end
  else
    hexnibble := '';
end;
function hexb(b : byte) : string;
begin
  hexb := hexnibble(b div 16) + hexnibble(b mod 16);
end;
function hexw(w : word) : string;
begin
  hexw := hexb(hi(w)) + hexb(lo(w));
end;
function hexl(l : longint) : string;
var
  w : array[0..1] of word absolute l;
begin
  hexl := hexw(w[1]) + hexw(w[0]);
end;
function hex(l : longint) : string;
var
  temp : string;
begin
  allnibbles := false;
  wasnonzero := false;
  temp := hexl(l);
  if temp = '' then
    temp := '0';
  hex := temp;
  allnibbles := true;
end;

function openfile(const name : string; var f : file; mode : word; doreset : boolean) : boolean;

function action : byte;
var
  ch : char;
begin
  writeln;
  writeln('Error accessing file ', name, '.');
  write('(A)bort, (R)etry: ');
  repeat
    ch := upcase(extreadkey);
  until ch in ['A', 'R', 'D'];
  case ch of
    'A' : action := 0;
    'R' : action := 1;
    'D' : action := 2;
  end;
  writeln(ch);
end;

var
  afm : word;

begin
  openfile := false;
  afm := filemode;
  filemode := mode;
  assign(f, name);
  repeat
    if doreset then
      reset(f, 1)
    else
      rewrite(f, 1);
    case ioresult of
      0 : begin
	    openfile := true;
	    break;
	  end;
      2, 3,
      5 : case action of
	    0 : break;
	    2 : begin
		  swapvectors;
		  exec(getenv('COMSPEC'), '');
		  swapvectors;
		end;
	  end;
    end;
  until false;

  filemode := afm;
end;

procedure abort(const s : string);
begin
  writeln(s);
  halt;
end;

procedure nextin;
begin
  inc(finpos, inblock);
  if inrest < blocksize then
    inblock := inrest
  else
    inblock := blocksize;
  blockread(fin, inbuf^, inblock);
  dec(inrest, inblock);
  inpos := 0;
end;

procedure commitout;
begin
  blockwrite(fout, outbuf^, outpos);
  inc(size, outpos);
  outpos := 0;
end;

procedure startinput;
begin
  finpos := 0;
  inpos := 0;
  inrest := filesize(fin);
  inblock := 0;
  skipped := 0;
  getmem(inbuf, blocksize);
  nextin;
end;

procedure startoutput;
begin
  outpos := 0;
  size := 0;
  getmem(outbuf, blocksize);
end;

procedure doneinput;
begin
  close(fin);
  freemem(inbuf, blocksize);
end;

procedure doneoutput;
begin
  commitout;
  close(fout);
  freemem(outbuf, blocksize);
end;

procedure checkbufs;
begin
  if inpos = inblock then
    nextin;
  if outpos = blocksize then
    commitout;
end;

procedure copybytes(cnt : word);
var
  now : longint;
begin
  if cnt < 1 then
    exit;
  repeat
    now := cnt;
    if now + inpos > inblock then
      now := inblock - inpos;
    if now + outpos > blocksize then
      now := blocksize - outpos;
    if now = 0 then
      halt(29);
    move(inbuf[inpos], outbuf[outpos], now);
    inc(inpos, now);
    inc(outpos, now);
    dec(cnt, now);
    checkbufs;
  until cnt = 0;
end;

function getbyte : byte;
begin
  getbyte := byte(inbuf[inpos]);
  inc(inpos);
  checkbufs;
end;

procedure putbyte(b : byte);
begin
  outbuf[outpos] := char(b);
  inc(outpos);
  checkbufs;
end;

function peek : byte;
begin
  peek := byte(inbuf[inpos]);
end;

function foutpos : longint;
begin
  foutpos := filepos(fout) + outpos;
end;

procedure get(cnt : byte; var out);
var
  data : pchar;
  i : byte;
begin
  data := pchar(@out);
  for i := 1 to cnt do
    data[i - 1] := char(getbyte);
end;

procedure skip(cnt : longint);
var
  i : longint;
begin
  for i := 1 to cnt do
    getbyte;
end;

procedure skipto(pos : longint);
begin
  skip(pos - finpos - inpos);
end;

procedure put(cnt : byte; var out);
var
  data : pchar;
  i : byte;
begin
  data := pchar(@out);
  for i := 1 to cnt do
    putbyte(byte(data[i - 1]));
end;

procedure getback(cnt : byte; var out);
var
  data : pchar;
  i : byte;
begin
  data := pchar(@out);
  for i := 1 to cnt do
    data[cnt - i] := char(getbyte);
end;

procedure putback(cnt : byte; const out);
var
  data : pchar;
  i : byte;
begin
  data := pchar(@out);
  for i := 1 to cnt do
    putbyte(byte(data[cnt - i]));
end;

procedure putbackl(cnt : byte; out : longint);
begin
  putback(cnt, out);
end;

function readdelta : longint;
var
  b : byte;
  delta : longint;
begin
  delta := 0;
  repeat
    b := getbyte;
    delta := delta shl 7 + b and $7F;
  until b < $80;
  readdelta := delta;
end;

procedure writedelta(delta : longint);
var
  i,
  b : byte;
  buf : array[1..10] of byte;
begin
  b := 0;
  repeat
    inc(b);
    buf[b] := (delta and $7F) or $80;
    delta := delta shr 7;
  until delta = 0;
  buf[1] := buf[1] and $7F;
  for i := b downto 1 do
    putbyte(buf[i]);
end;


procedure writemidiheader(tracks : word);
const
  headerid : array[1..4] of char = 'MThd';
begin
  put(4, headerid);	{ MThd }
  putbackl(4, 6);	{ Chunklen }
  putbackl(2, 1);	{ SMF Type; 1=multiple concurrent tracks }
  putbackl(2, tracks);	{ number of tracks }
  putbackl(2, 120);	{ delta's per quarter }
end;

var tracksizepos : longint;	{ Holds track size }
procedure writetrackheader;
const
  headerid : array[1..4] of char = 'MTrk';
begin
  put(4, headerid);	{ MThd }
  tracksizepos := foutpos;
  putbackl(4, 0);
end;

procedure finishtrack;	{ Write track len }
var
  oldpos : longint;
begin
  commitout;
  oldpos := filepos(fout);

  seek(fout, tracksizepos);
  putbackl(4, oldpos - tracksizepos - 4);
  commitout;

  seek(fout, oldpos);
end;

procedure writeconductortrack;
var
  sizepos : longint;
const
  tempo : array[1..4] of byte = (0, $FF, $51, 3);
  times : array[1..4] of byte = (0, $FF, $58, 4);
  eoftr : array[1..4] of byte = (0, $FF, $2F, 0);
begin
  writetrackheader;

  put     (4, tempo);	{ Set tempo }
  putbackl(3, 500000);	{ Microseconds per beat }

  put     (4, times);	{ Set time signature }
  putbackl(2, $0402);	{ 4/(2^2) beat }
  putbackl(1, 24);	{ Midi clocks (delta times) per beat }
  putbackl(1, 8);	{ 32nd's per quarter }

  put	  (4, eoftr);	{ End of Track }

  finishtrack;
end;

procedure convert(const fromname, toname : string);
var
  isfirstvolchange,
  trackdone : boolean;
  laststatus,
  status : byte;
  curtime,
  lasttime : longint;
  hangingnotes : phangingnotes;
  notetimes : plongarray;
  nextnote : word;

procedure putevent;
begin
  writedelta((curtime - lasttime) * 2);
  lasttime := curtime;
  if status <> laststatus then
    putbyte(status);
  laststatus := status;
end;

procedure storehangingnote(voice, note, vol : byte; dur : longint);
var
  i : word;
begin
	{ Store the note, so that it will be released in time }
  for i := 1 to high(hangingnotes^) - 1 do
    if hangingnotes^[i, 4] = 0 then
      begin
	hangingnotes^[i, 1] := status and $F;
	hangingnotes^[i, 2] := note;
	hangingnotes^[i, 3] := vol;
	hangingnotes^[i, 4] := 1;
	notetimes^[i] := curtime + dur;

	if curtime + dur < notetimes^[nextnote] then
	  nextnote := i;
	break;
      end;
end;

procedure noteon;
var
  note,
  vol : byte;
  dur : longint;
begin
  putevent;

  note := getbyte;
  vol := getbyte;
  dur := readdelta;

  putbyte(note);
  putbyte(vol);

  storehangingnote(status and $F, note, vol, dur);
end;

procedure controlchange;
var
  controller,
  value : byte;
begin
  controller := getbyte;
  value := getbyte;

  if isfirstvolchange and
     (status = $B0) and
     (controller = 7) and
     (value = 127) then
    begin
      isfirstvolchange := false;
      exit;
    end;

  if (status = $B0) and
     (controller = 105) then
    exit;

  putevent;

  putbyte(controller);
  putbyte(value);
end;

procedure programchange;
begin
  putevent;

  copybytes(1);
end;

procedure aftertouch;
begin
  putevent;

  copybytes(1);
end;

procedure pitchbender;
begin
  putevent;

  copybytes(2);
end;

procedure systemevent;
var
  meta,
  data : byte;
  len : longint;
begin
	{ Events to be filtered }
  case status of
    $FE: begin
	   meta := getbyte;
	   case meta of
	     $10: begin
		    skip(2);
		    skip(4 + getbyte);
		  end;
	     $12: skip(2);
	     $13: skip(10);
	     $14: skip(2);
	     $15: skip(6);
	   else
	     abort('Unknown $FE event ' + hexb(meta) + ' at ' + hex(finpos + inpos) + '.');
	   end;
	   exit;
	 end;
  end;

  putevent;

  case status of
    $F0,			{ SysEx }
    $F7: repeat			{ SysEx cont'd }
	   data := getbyte;
	   putbyte(data);
	 until data = $F7;
    $FF: begin			{ Meta event }
	   meta := getbyte;
	   putbyte(meta);
	   len := readdelta;
	   writedelta(len);
	   copybytes(len);

	   if meta = $2F then  	{ Track end }
	     trackdone := true;
	 end;
  else
    abort('Unknown system event ' + hexb(status) + ' at ' + hex(finpos + inpos) + '.');
  end;
end;

procedure checkhangingnotes;
var
  oldcurtime : longint;
  oldstatus : byte;
  i : word;
  nexttime : longint;
begin
  if curtime < notetimes^[nextnote] then
    exit;

  oldcurtime := curtime;
  oldstatus := status;

  repeat
    curtime := notetimes^[nextnote];
    status := $80 or hangingnotes^[nextnote, 1];
    putevent;		{ put delay and status byte }

    putbyte(hangingnotes^[nextnote, 2]);	{ note }
    putbyte(0);					{ vol }

    hangingnotes^[nextnote, 4] := 0;		{ mark as unused }

    nexttime := maxlongint;			{ find next note }
    for i := low(notetimes^) to high(notetimes^) do
      if (hangingnotes^[i, 4] = 1) and
	 (notetimes^[i] < nexttime) then
	begin
	  nextnote := i;
	  nexttime := notetimes^[i];
	end;

  until oldcurtime < notetimes^[nextnote];

  curtime := oldcurtime;
  status := oldstatus;
end;

var
  track,
  tracks : word;
  overhead,
  trackpos : array[1..maxtracks] of longint;
  trackdataofs,
  tracksize,
  curdelay : longint;
  evcntr : byte;

procedure writepercent(backspace : boolean);
begin
  if backspace then
    write(#8#8#8#8);

  write(100 * (finpos + inpos - overhead[track])
	  div (trackpos[tracks + 1] - overhead[tracks]):3, '%');
end;

begin
  if not openfile(fromname, fin, OF_READ or OF_SHARE_DENY_NONE, true) or
     not openfile(toname, fout, OF_WRITE or OF_SHARE_DENY_WRITE, false) then
    exit;

  new(hangingnotes);
  new(notetimes);
  fillchar(hangingnotes^, sizeof(hangingnotes^), 0);
  fillchar(notetimes^, sizeof(notetimes^), 0);
  nextnote := high(notetimes^);
  notetimes^[nextnote] := maxlongint - 10;
  hangingnotes^[nextnote, 4] := 1;

  startinput;
  startoutput;

	{ First read only track infos from .hmi file }
  skip($E4);
  get(2, tracks);
  if tracks > maxtracks then
    begin
      writeln('Too many tracks! Only ', maxtracks, ' converted.');
      tracks := maxtracks;
    end;

  skipto($172);
  for track := 1 to tracks do
    get(4, trackpos[track]);
  trackpos[tracks + 1] := filesize(fin) - $10;

  for track := 1 to tracks do
    begin
      skipto(trackpos[track] + $57);
      get(4, trackdataofs);

      if track = 1 then
	overhead[track] := trackpos[track]
      else
	overhead[track] := overhead[track - 1];

      inc(overhead[track], trackdataofs);
    end;

  overhead[tracks + 1] := overhead[tracks];
  { + trackpos[tracks + 1] - trackpos[tracks];}

	{ Reopen after reading track infos }
  doneinput;
  openfile(fromname, fin, OF_READ or OF_SHARE_DENY_NONE, true);
  startinput;

  write('Writing Midi header info...');

  writemidiheader(tracks + 1);

  writeconductortrack;

  write(#13#9#9#9#9#9#9#9#13);

  evcntr := 0;

  skipped := trackpos[1];

  for track := 1 to tracks do
    begin
      skipto(trackpos[track]);
      write(#13'Converting track ', track, '/', tracks, ': ');

      writetrackheader;

      skip($57);
      get(4, curdelay);
      inc(skipped, curdelay);
      skip(curdelay - 4 - $57);

      writepercent(false);

      trackdone := false;
      curtime := 0;
      lasttime := 0;
      status := 0;
      laststatus := 0;
      isfirstvolchange := true;

      repeat
	if evcntr mod 10 = 0 then
	  writepercent(true);
	inc(evcntr);
	{$IFDEF DEBUG} {$ENDIF}
	{$IFDEF DEBUG} write(#13#9#9'Event at ', hex(finpos + inpos), #13); {$ENDIF}

	curdelay := readdelta;
	inc(curtime, curdelay);

	checkhangingnotes;	{ Turn off notes that are done }

	if peek >= $80 then
	  status := getbyte;	{ Otherwise keep old status byte }

	case status shr 4 of
	  $9: noteon;
	  $B: controlchange;
	  $C: programchange;
	  $D: aftertouch;
	  $E: pitchbender;
	  $F: systemevent;
	else
	  begin
	    writeln('Status code ', hexb(status), ' at ', hex(finpos + inpos) + ' not supported.');
	    status := $FF;
	    putevent;
	    putbyte($2F);
	    putbyte(0);
	    break;
	  end;
	end;
      until trackdone;

      finishtrack;
    end;

  write(#13#9#9#9#9#9#9#9#13);

  doneoutput;
  doneinput;

  dispose(notetimes);
  dispose(hangingnotes);
end;

var
  f : searchrec;
  d,
  d2,
  n,
  e : string;
begin
  writeln('HMI2MID V1.0, Copyright (C) 1999 by Josef Drexler <jdrexler@julian.uwo.ca>'#13#10);
  fsplit(paramstr(1), d, n, e);
  findfirst(paramstr(1), anyfile - directory, f);

  if doserror <> 0 then
    begin
      writeln('Usage:	HMI2MID <HMI-Files> [Destination]'#13#10 +
	    '	HMI-Files: HMI-Files to be converted. * and ? are ok.'#13#10 +
	    '	Destination: Directory to put the midi files in. Same as location'#13#10 +
	    '		of HMI-Files if not specified.'#13#10#13#10);

      abort('Copy and use this program freely, as long as you don''t change it and give me'#13#10 +
	    'credit for it.');
    end;

  while doserror = 0 do
    begin
      fsplit(f.name, d2, n, e);
      if paramcount > 1 then
	begin
	  d2 := paramstr(2);
	  if d2[byte(d2[0])] <> '\' then
	    d2 := d2 + '\';
	end
      else
	d2 := d;
      e := '.mid';
      writeln('Converting ', d+f.name, ' to ', d2+n+e);
      convert(d+f.name, d2+n+e);
      findnext(f);
    end;
end.
