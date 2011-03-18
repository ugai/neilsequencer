/*
  
  The mda VST plug-ins are released under the MIT license or under the GPL
  "either version 2 of the License, or (at your option) any later version".
  
*/

#include "mdaEPianoData.h"
#include "epiano.h"
#include <lunar/fx.hpp>
#include <lunar/dsp.h>

#define NPARAMS 12       //number of parameters
#define NPROGS   8       //number of programs
#define NOUTS    2       //number of outputs
#define NVOICES 32       //max polyphony
#define SUSTAIN 128
#define SILENCE 0.0001f  //voice choking
#define WAVELEN 422414   //wave data bytes

#define EVENTBUFFER 120
#define EVENTS_DONE 99999999

struct VOICE  //voice state
{
  long  delta;  //sample playback
  long  frac;
  long  pos;
  long  end;
  long  loop;
  
  float env;  //envelope
  float dec;

  float f0;   //first-order LPF
  float f1;
  float ff;

  float outl;
  float outr;
  long  note; //remember what note triggered this
};

struct KGRP  //keygroup
{
  long  root;  //MIDI root note
  long  high;  //highest note
  long  pos;
  long  end;
  long  loop;
};


class epiano : public lunar::fx<epiano> {
public:
  float param[NPARAMS];
  float Fs, iFs;
	
#define EVENTBUFFER 120
#define EVENTS_DONE 99999999
  long notes[EVENTBUFFER + 8];  //list of delta|note|velocity for current block
	
  ///global internal variables
  KGRP  kgrp[34];
  VOICE voice[NVOICES];
  long  poly;
  short *waves;
  float width;
  long  size, sustain;
  float lfo0, lfo1, dlfo, lmod, rmod;
  float treb, tfrq, tl, tr;
  float tune, fine, random, stretch, overdrive;
  float muff, muffvel, sizevel, velsens, volume, modwhl;

  void init() {
    waves = epianoData;
    
      //Waveform data and keymapping
      kgrp[ 0].root = 36;  kgrp[ 0].high = 39; //C1
      kgrp[ 3].root = 43;  kgrp[ 3].high = 45; //G1
      kgrp[ 6].root = 48;  kgrp[ 6].high = 51; //C2
      kgrp[ 9].root = 55;  kgrp[ 9].high = 57; //G2
      kgrp[12].root = 60;  kgrp[12].high = 63; //C3
      kgrp[15].root = 67;  kgrp[15].high = 69; //G3
      kgrp[18].root = 72;  kgrp[18].high = 75; //C4
      kgrp[21].root = 79;  kgrp[21].high = 81; //G4
      kgrp[24].root = 84;  kgrp[24].high = 87; //C5
      kgrp[27].root = 91;  kgrp[27].high = 93; //G5
      kgrp[30].root = 96;  kgrp[30].high =999; //C6
		
      kgrp[0].pos = 0;        kgrp[0].end = 8476;     kgrp[0].loop = 4400;  
      kgrp[1].pos = 8477;     kgrp[1].end = 16248;    kgrp[1].loop = 4903;  
      kgrp[2].pos = 16249;    kgrp[2].end = 34565;    kgrp[2].loop = 6398;  
      kgrp[3].pos = 34566;    kgrp[3].end = 41384;    kgrp[3].loop = 3938;  
      kgrp[4].pos = 41385;    kgrp[4].end = 45760;    kgrp[4].loop = 1633; //was 1636;  
      kgrp[5].pos = 45761;    kgrp[5].end = 65211;    kgrp[5].loop = 5245;  
      kgrp[6].pos = 65212;    kgrp[6].end = 72897;    kgrp[6].loop = 2937;  
      kgrp[7].pos = 72898;    kgrp[7].end = 78626;    kgrp[7].loop = 2203; //was 2204;  
      kgrp[8].pos = 78627;    kgrp[8].end = 100387;   kgrp[8].loop = 6368;  
      kgrp[9].pos = 100388;   kgrp[9].end = 116297;   kgrp[9].loop = 10452;  
      kgrp[10].pos = 116298;  kgrp[10].end = 127661;  kgrp[10].loop = 5217; //was 5220; 
      kgrp[11].pos = 127662;  kgrp[11].end = 144113;  kgrp[11].loop = 3099;  
      kgrp[12].pos = 144114;  kgrp[12].end = 152863;  kgrp[12].loop = 4284;  
      kgrp[13].pos = 152864;  kgrp[13].end = 173107;  kgrp[13].loop = 3916;  
      kgrp[14].pos = 173108;  kgrp[14].end = 192734;  kgrp[14].loop = 2937;  
      kgrp[15].pos = 192735;  kgrp[15].end = 204598;  kgrp[15].loop = 4732;  
      kgrp[16].pos = 204599;  kgrp[16].end = 218995;  kgrp[16].loop = 4733;  
      kgrp[17].pos = 218996;  kgrp[17].end = 233801;  kgrp[17].loop = 2285;  
      kgrp[18].pos = 233802;  kgrp[18].end = 248011;  kgrp[18].loop = 4098;  
      kgrp[19].pos = 248012;  kgrp[19].end = 265287;  kgrp[19].loop = 4099;  
      kgrp[20].pos = 265288;  kgrp[20].end = 282255;  kgrp[20].loop = 3609;  
      kgrp[21].pos = 282256;  kgrp[21].end = 293776;  kgrp[21].loop = 2446;  
      kgrp[22].pos = 293777;  kgrp[22].end = 312566;  kgrp[22].loop = 6278;  
      kgrp[23].pos = 312567;  kgrp[23].end = 330200;  kgrp[23].loop = 2283;  
      kgrp[24].pos = 330201;  kgrp[24].end = 348889;  kgrp[24].loop = 2689;  
      kgrp[25].pos = 348890;  kgrp[25].end = 365675;  kgrp[25].loop = 4370;  
      kgrp[26].pos = 365676;  kgrp[26].end = 383661;  kgrp[26].loop = 5225;  
      kgrp[27].pos = 383662;  kgrp[27].end = 393372;  kgrp[27].loop = 2811;  
      kgrp[28].pos = 383662;  kgrp[28].end = 393372;  kgrp[28].loop = 2811; //ghost
      kgrp[29].pos = 393373;  kgrp[29].end = 406045;  kgrp[29].loop = 4522;  
      kgrp[30].pos = 406046;  kgrp[30].end = 414486;  kgrp[30].loop = 2306;  
      kgrp[31].pos = 406046;  kgrp[31].end = 414486;  kgrp[31].loop = 2306; //ghost
      kgrp[32].pos = 414487;  kgrp[32].end = 422408;  kgrp[32].loop = 2169;  
		
      //extra xfade looping...
      for(long k=0; k<28; k++)
	{
	  long p0 = kgrp[k].end;
	  long p1 = kgrp[k].end - kgrp[k].loop;
			
	  float xf = 1.0f;
	  float dxf = -0.02f;
			
	  while(xf > 0.0f)
	    {
	      waves[p0] = (short)((1.0f - xf) * (float)waves[p0] + xf * (float)waves[p1]);
	      p0--;
	      p1--;
	      xf += dxf;
	    }
	}
		
      //initialise...
      for(long v=0; v<NVOICES; v++) 
	{
	  voice[v].note = 0;
	  voice[v].env = 0.0f;
	  voice[v].dec = 0.99f; //all notes off
	}
      notes[0] = EVENTS_DONE;
      volume = 0.2f;
      muff = 160.0f;
      sustain = 0;
      tl = tr = lfo0 = dlfo = 0.0f;
      lfo1 = 1.0f;
      
	sizevel = 0;	// this is uninitialized in the original epiano (?)
	//update();
	
	Fs = transport->samples_per_second;
	iFs = 1.0f / Fs;
	dlfo = 6.283f * iFs * (float)exp(6.22f * param[5] - 2.61f); //lfo rate 
  }
  
  void update()  //parameter change
  {
    size = (long)(12.0f * param[2] - 6.0f);
		
    treb = 4.0f * param[3] * param[3] - 1.0f; //treble gain
    if(param[3] > 0.5f) tfrq = 14000.0f; else tfrq = 5000.0f; //treble freq
    tfrq = 1.0f - (float)exp(-iFs * tfrq);
		
    rmod = lmod = param[4] + param[4] - 1.0f; //lfo depth
    if(param[4] < 0.5f) rmod = -rmod;
		
    dlfo = 6.283f * iFs * (float)exp(6.22f * param[5] - 2.61f); //lfo rate
		
    velsens = 1.0f + param[6] + param[6];
    if(param[6] < 0.25f) velsens -= 0.75f - 3.0f * param[6];
		
    width = 0.03f * param[7];
    poly = 1 + (long)(31.9f * param[8]);
    fine = param[9] - 0.5f;
    random = 0.077f * param[10] * param[10];
    stretch = 0.0f; //0.000434f * (param[11] - 0.5f); parameter re-used for overdrive!
    overdrive = 1.8f * param[11];
  }
  
  void noteOn(long note, long velocity, long vl)
  {
    float l=99.0f;
    long  v, k, s;
	  
    if(velocity > 0) 
      {
	voice[vl].f0 = voice[vl].f1 = 0.0f;	// since we're not doing polyphony, this is the remainder of the voice-picking code
	
	k = (note - 60) * (note - 60);
	l = fine + random * ((float)(k % 13) - 6.5f);  //random & fine tune
	if(note > 60) l += stretch * (float)k; //stretch
	
	s = size;
	if(velocity > 40) s += (long)(sizevel * (float)(velocity - 40));  
	
	k = 0;
	while(note > (kgrp[k].high + s)) k += 3;  //find keygroup
	l += (float)(note - kgrp[k].root); //pitch
	l = 32000.0f * iFs * (float)exp(0.05776226505 * l);
	voice[vl].delta = (long)(65536.0f * l);
	voice[vl].frac = 0;
	
	if(velocity > 48) k++; //mid velocity sample
	if(velocity > 80) k++; //high velocity sample
	voice[vl].pos = kgrp[k].pos;
	voice[vl].end = kgrp[k].end - 1;
	voice[vl].loop = kgrp[k].loop;
	
	voice[vl].env = (3.0f + 2.0f * velsens) * (float)pow(0.0078f * velocity, velsens); //velocity
	    
	if(note > 60) voice[vl].env *= (float)exp(0.01f * (float)(60 - note)); //new! high notes quieter
	
	l = 50.0f + param[4] * param[4] * muff + muffvel * (float)(velocity - 64); //muffle
	if(l < (55.0f + 0.4f * (float)note)) l = 55.0f + 0.4f * (float)note;
	if(l > 210.0f) l = 210.0f;
	voice[vl].ff = l * l * iFs;
	
	voice[vl].note = note; //note->pan
	if(note <  12) note = 12;
	if(note > 108) note = 108;
	l = volume;
	voice[vl].outr = l + l * width * (float)(note - 60);
	voice[vl].outl = l + l - voice[vl].outr;
	
	if(note < 44) note = 44; //limit max decay length
	voice[vl].dec = (float)exp(-iFs * exp(-1.0 + 0.03 * (double)note - 2.0f * param[0]));
      }
    else //note off
      {
	    
	if(sustain==0)
	  {
	    voice[vl].dec = (float)exp(-iFs * exp(6.0 + 0.01 * (double)note - 5.0 * param[1]));
	  }
	else voice[vl].note = SUSTAIN;
      }
      } 
  
  
  void check_parameter(int p, float* i, bool& changed) {
    if (i) {
      param[p] = *i;
	changed = true;
	  }
      }

  void process_events() {
    bool needs_update = false;
      check_parameter(0, globals->envdecay, needs_update);
	check_parameter(1, globals->envrelease, needs_update);
	  check_parameter(2, globals->hardness, needs_update);
	    check_parameter(3, globals->trebleboost, needs_update);
	      check_parameter(4, globals->modulation, needs_update);
		check_parameter(5, globals->lforate, needs_update);
		  check_parameter(6, globals->velsense, needs_update);
		    check_parameter(7, globals->stereowidth, needs_update);
		      check_parameter(8, globals->poly, needs_update);
			check_parameter(9, globals->finetune, needs_update);
			  check_parameter(10, globals->randomtune, needs_update);
			    check_parameter(11, globals->overdrive, needs_update);
			      
			      if (needs_update)
				update();
				
				int event = 0;
				  for (int i = 0; i < track_count; i++) {
				    long velocity = 127;
				      if (tracks[i].volume) velocity = *tracks[i].volume;
					
					if (tracks[i].note) { 
					  notes[event++] = 1;
					    if (*tracks[i].note == 0.0f) {
					      notes[event++] = voice[i].note;
					      notes[event++] = 0;
						} else {
					      notes[event++] = *tracks[i].note;
					      notes[event++] = velocity;
						}
					    notes[event++] = i;
					      }				
					  }
				    notes[event] = EVENTS_DONE;
  }

  void process_stereo(float *inL, float *inR, float *outL, float *outR, int sampleFrames) {
    
    float* out0 = outL;
    float* out1 = outR;
    long event=0, frame=0, frames, v;
    float x, l, r, od=overdrive;
    long i;
	
    while(frame<sampleFrames)
      {
	frames = notes[event++];
	if(frames>sampleFrames) frames = sampleFrames;
	frames -= frame;
	frame += frames;
			
	while(--frames>=0)
	  {
	    VOICE *V = voice;
	    l = r = 0.0f;
				
	    for(v=0; v<track_count; v++)
	      {
		if (V->note == 0) {
		  V++;
		    continue;
		      }
		V->frac += V->delta;  //integer-based linear interpolation
		V->pos += V->frac >> 16;
		V->frac &= 0xFFFF;
		if(V->pos > V->end) V->pos -= V->loop;
		//i = waves[V->pos];
		//i = (i << 7) + (V->frac >> 9) * (waves[V->pos + 1] - i) + 0x40400000;  //not working on intel mac !?!
		//x = V->env * (*(float *)&i - 3.0f);  //fast int->float
		//x = V->env * (float)i / 32768.0f;      
		i = waves[V->pos] + ((V->frac * (waves[V->pos + 1] - waves[V->pos])) >> 16);
		x = V->env * (float)i / 32768.0f;
					
		V->env = V->env * V->dec;  //envelope
					
		if(x>0.0f) { x -= od * x * x;  if(x < -V->env) x = -V->env; } //+= 0.5f * x * x; } //overdrive
					
		l += V->outl * x;
		r += V->outr * x;
					
		V++;
	      }
	    tl += tfrq * (l - tl);  //treble boost
	    tr += tfrq * (r - tr);
	    r  += treb * (r - tr);
	    l  += treb * (l - tl);
				
	    lfo0 += dlfo * lfo1;  //LFO for tremolo and autopan
	    lfo1 -= dlfo * lfo0;
	    l += l * lmod * lfo1;
	    r += r * rmod * lfo1;  //worth making all these local variables?
	    
	      *out0++ = l;
	      *out1++ = r;
	  }
			
	if(frame<sampleFrames)
	  {
	    if(track_count == 0 && param[4] > 0.5f) 
	      { lfo0 = -0.7071f;  lfo1 = 0.7071f; } //reset LFO phase - good idea?
	    long note = notes[event++];
	    long vel  = notes[event++];
	      long voice = notes[event++];
		noteOn(note, vel, voice);
	  }
      }
    if(abs(tl)<1.0e-10) tl = 0.0f; //anti-denormal
    if(abs(tr)<1.0e-10) tr = 0.0f;
		
    for(v=0; v<track_count; v++) if(voice[v].env < SILENCE) voice[v].note = 0;
    notes[0] = EVENTS_DONE;  //mark events buffer as done
  }
};

lunar_fx *new_fx() { return new epiano(); }
