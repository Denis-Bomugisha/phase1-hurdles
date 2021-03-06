#!/usr/bin/env python

# This file generates a band plan for the Hurdle 2 transmitter.
#
# The output is a configuration file that will be read by the
# transmit flowgraph and used to instantiate the transmitters.
#
# All configuration of the generator is done here, inline.



#------------------------
# Problem Statement
#------------------------

# The problem statement from the hurdle document is:
# Develop a classifier that can identify the occupied
# range and type of six simultaneous non-overlapping
# signals within a 3 MHz bandwidth channel. Each signal
# will be continuous in time and fixed in frequency for
# the duration of the test vector. The signals that may
# be present are: analog FM, QPSK, and GMSK.
# Multiple or no instances of a particular signal type
# may be present. Each signal is present at the same
# total power as each of the others. AWGN is present
# in the 3 MHz channel. The SNR seen by any individual
# signal type will be greater than or equal to 15 dB.

#------------------------
# Caveats
#------------------------
#
# Based on our understanding, "SNR" is defined as signal power of the
# transmitted modulation divided by the noise power within the 99% 
# bandwidth of the signal.
#
# The generator does not guarantee at least one type of
# each modulator, it is uniformly selected so you may end
# up with instances without some types

#------------------------
# System Configuration
#------------------------

# Total bandwidth of the channel
#channel_bandwidth = 3e6

# The number of bins to divide the channel into
#n_bins = 30

# The number of signals to generate
#n_signals = 6

# Minimum SNR in dB
#min_snr_db = 15

# Valid signal types
#signal_types = ('FM','QPSK','GMSK')

# Random generator seed.  Set to "None" for random selection
#instance_seed = None

#Maximum width of a signal in bins
#max_signal_bins= 4

#Maximum number of attempts before aborting
#max_tries = 100

#------------------------
# Main Process
#
# Don't change anything below this line
#------------------------

import random
import json
#------------------------
# Parameter Calculation
#------------------------

def generate_band_plan(channel_bandwidth, n_bins, n_signals, min_snr_db,
                       max_snr_db, signal_types, instance_seed, max_signal_bins,
                       max_tries ):


    #------------------------
    # Parameter Calculation
    #------------------------
    
    bin_bandwidth = channel_bandwidth/n_bins
    bin_edges = [ i*bin_bandwidth -channel_bandwidth/2.0 
                 for i in range(n_bins+1)]
    bin_centers = [ i*bin_bandwidth + bin_bandwidth/2.0 -channel_bandwidth/2.0
                   for i in range(n_bins)]
    
    #------------------------
    # Signal Generation
    #------------------------
    
    random.seed(instance_seed)
    
    signals = list() #Store the signals we generate
    tries = 0
    
    valid_bins = set(range(n_bins))
    
    
    
    while (len(signals) < n_signals) and (tries < max_tries):
        tries+=1
        signal = dict()
    
        #Randomly generate a bandwidth
        signal['n_bins'] = random.randint(1, max_signal_bins)
        
        # randomly generate an SNR not lower than the min_snr_dB
        signal['snr'] = random.uniform(min_snr_db, max_snr_db) 
        
        # Randomly generate a center frequency
        # Simplify things for now. Odd numbers of bins get a center frequency
        # centered on the center bin, even numbers of bins get a center 
        # frequency in the middle of the center 2 bins
        if signal['n_bins'] % 2 == 0:
            # 0 Hz and the max frequency edge are never valid
            num_invalid_edges = int(signal['n_bins']/2)
            valid_edges = bin_edges[num_invalid_edges:n_bins-num_invalid_edges]
            signal['center_freq'] = random.choice(valid_edges)
            
            # get the index for the center freq
            edge_ind = bin_edges.index(signal['center_freq'])
            
            signal['occupied_bins'] = set( \
                edge_ind - num_invalid_edges + x \
                for x in range(0,signal['n_bins']) )
        
        # otherwise there's an odd number of bins
        else:
            # rounding down
            num_invalid_bins = int(signal['n_bins']/2)
            valid_centers = bin_centers[num_invalid_bins:n_bins-num_invalid_bins]
            signal['center_freq'] = random.choice(valid_centers)
            
            # get the index for the center freq
            bin_ind = bin_centers.index(signal['center_freq'])
            
            signal['occupied_bins'] = set( \
                bin_ind - num_invalid_bins + x \
                for x in range(0,signal['n_bins']) )
            
        
        # ensuring guard bins wrap around in the frequency domain correctly
        signal['guard_bins'] = set([ (min(signal['occupied_bins'])-1)%n_bins,
                                     (max(signal['occupied_bins'])+1)%n_bins]
                                  )
        
        # limit guard bins to being within valid bins
        signal['guard_bins'] &= valid_bins
        
        #Verify that we aren't stepping on an existing signal
        overlaps = False
        for existing in signals:
            occupied_or_guard = existing['occupied_bins'] | existing['guard_bins'] 
            if( len(signal['occupied_bins'] & occupied_or_guard) >0 ):
                #print "[%d tries] This signal overlaps an existing one, retrying..." % tries
                overlaps=True
                break
        if( overlaps == True): continue
    
        #Randomly generate a signal type
        signal['modulation_type'] = random.choice(signal_types)
    
        #Add this signal to the primary list
        signals.append(signal)
    
    # Get rid of the sets, since they're python specific
    for signal in signals:
        signal['occupied_bins'] = list(signal['occupied_bins'])
        signal['guard_bins'] = list(signal['guard_bins'])
    
    # Print out the bands
    if(False):
        print("\n\nGenerated the following %d signals" % len(signals))
        for signal in signals:
            print(signal)
    
    # Write out the plan
    band_plan = dict()
    
    band_plan['freq_span'] = channel_bandwidth
    band_plan['n_bins']    = n_bins
    band_plan['n_signals'] = len(signals)
    band_plan['signals'] = signals

    return band_plan


def save_band_plan(band_plan, filename='band_data.json'):

    # Writing JSON data
    with open(filename, 'w') as f:
        json.dump(band_plan, f)
