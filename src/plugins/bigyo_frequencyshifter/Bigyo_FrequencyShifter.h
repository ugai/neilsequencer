/*
Copyright (C) 2007 Marcin Dabrowski

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
*/
#pragma once

#pragma pack(1)                        

struct gvals {
	unsigned short Rate;
	unsigned char DirectionL;
	unsigned char DirectionR;
};

struct avals {
	int nonlinearity;
	int maxfreq;
};

#pragma pack()

class freqshifter : public zzub::plugin {
public:
	freqshifter();
	virtual ~freqshifter();
	virtual void process_events();
	virtual void process_controller_events() {}
	virtual void init(zzub::archive * pi);
	//virtual bool MDKWork(float *psamples, int numsamples, int const mode);
	virtual bool process_stereo(float** pin, float** pout, int numsamples, int mode);
	virtual void command(int i);
	virtual void load(zzub::archive *arc) {}
	virtual void save(zzub::archive * po);
	virtual const char* describe_value(int param, int value);

	virtual void attributes_changed();

	virtual void destroy() { delete this; }
	virtual void stop() {}
	virtual void set_track_count(int i) { }
	virtual void mute_track(int) {}
	virtual bool is_track_muted(int) const { return false; }
	virtual void midi_note(int channel, int note, int velocity) {}
	virtual void event(unsigned int) {}
	virtual const zzub::envelope_info** get_envelope_infos() { return 0; }
	virtual bool play_wave(int, int, float) { return false; }
	virtual void stop_wave() {}
	virtual int get_wave_envelope_play_position(int) { return -1; }
	virtual const char* describe_param(int) { return 0; }
	virtual bool set_instrument(const char*) { return false; }
	virtual void get_sub_menu(int, zzub::outstream*) {}
	virtual void add_input(const char*) {}
	virtual void delete_input(const char*) {}
	virtual void rename_input(const char*, const char*) {}
	virtual void input(float**, int, float) {}
	virtual void midi_control_change(int, int, int) {}
	virtual bool handle_input(int, int, int) { return false; }

	avals aval;
	gvals gval;

	inline float dB2lin(float dB)  {return powf(10.0f, dB/20.0f);}
	inline float lin2dB(float lin) {return 20.0f*log10f(lin);}
	inline float freq2omega(float freq) {return (float) (2.0f * M_PI * freq/_master_info->samples_per_second);}
	inline float freq2rate(float freq) {return  (2.0f * (float) freq/_master_info->samples_per_second);}
	inline float msec2samples(float msec) {return  (((float) _master_info->samples_per_second) * msec * 0.001f) ;}
	inline float lin2log(float value,float minlin,float maxlin,float minlog,float maxlog) { return minlog * (float) pow (maxlog/minlog, (value-minlin) / (maxlin-minlin));}
	
	HilbertPair hL, hR;
	FastCosSin carrier;
	
	int dirL, dirR;

	float slope;
	float rate;
	float MaxRate;
};

struct machine_info : zzub::info {
	machine_info();
	virtual zzub::plugin* create_plugin() const { return new freqshifter(); }
	virtual bool store_info(zzub::archive *data) const { return false; }
} _machine_info;

struct freqshifterplugincollection : zzub::plugincollection {
	virtual void initialize(zzub::pluginfactory *factory) { factory->register_info(&_machine_info); }
	virtual const zzub::info *get_info(const char *uri, zzub::archive *data) { return 0; }
	virtual void destroy() { delete this; }
	virtual const char *get_uri() { return 0; }
	virtual void configure(const char *key, const char *value) {}
};
