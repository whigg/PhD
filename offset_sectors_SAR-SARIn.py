import os
import functions as funct
import numpy as np
import matplotlib.pyplot as pl
from datetime import date

average_circumpolar_offset_SAR_SARIn = np.zeros(12)

WEDD_timeseries_SAR_SARIn = []
IND_timeseries_SAR_SARIn = []
ROSS_timeseries_SAR_SARIn = []
AMBEL_timeseries_SAR_SARIn = []
timeseries_SAR_SARIn = []

dates = []

for year in ['2011', '2012', '2013', '2014', '2015', '2016']:
    print(year)
    
    monthly_offset_WEDD_SAR_SARIn = []
    monthly_offset_IND_SAR_SARIn = []
    monthly_offset_ROSS_SAR_SARIn = []
    monthly_offset_AMBEL_SAR_SARIn = []
    monthly_offset_SAR_SARIn = []

    hist_offset_WEDD_SAR_SARIn = []
    hist_offset_IND_SAR_SARIn = []
    hist_offset_ROSS_SAR_SARIn = []
    hist_offset_AMBEL_SAR_SARIn = []
    hist_offset_circum_SAR_SARIn = []

    month_number = []

    for month in ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']:
        offset_WEDD_SAR_SARIn = []
        offset_IND_SAR_SARIn = []
        offset_ROSS_SAR_SARIn = []
        offset_AMBEL_SAR_SARIn = []
        circum_offset_SAR_SARIn = []
        
        dates.append(date(int(year), int(month), 15))
        
        if os.path.isdir('/Volumes/My Passport/Data/elev_files/' + year + month + '_MERGE'):
            os.chdir('/Volumes/My Passport/Data/elev_files/' + year + month + '_MERGE')
            month_number.append(int(month))
            print(month)
            for file in os.listdir():
                # 200 points equals the decorrelation scale (50 km)
                SC = 100
                SAR_to_SARIn = [1] * SC + [2] * SC
                SARIn_to_SAR = [2] * SC + [1] * SC
                
                len_bound = len(SAR_to_SARIn)   
                
                ssha_pre = []
                lon_pre = []
                lat_pre = []
                surface_pre = []
                f = open(file, 'r')
                for line in f:
                    line = line.strip()
                    columns = line.split()
                    # If data point is listed as 'valid'
                    if columns[1] == '1':
                        # If data point is from open ocean (1) or from a lead (2)
                        if columns[0] == '1' or columns[0] == '2':
                            # If the ssh point is less than 3 m from the mssh
                            if abs(float(columns[7]) - float(columns[8])) < .3:
                                    lat_pre.append(float(columns[5]))
                                    lon_pre.append(float(columns[6]))
                                    surface_pre.append(int(columns[0]))
                                    ssha_pre.append(float(columns[7]) - float(columns[8]))
                f.close()
                
                descending = np.where(np.gradient(lat_pre) < 0.)[0]
                if len(descending) > 10:
                    inflection = descending[-1]
                    #### Descending ####
                
                    ssha_desc = np.array(ssha_pre[:inflection])
                    lat_desc = np.array(lat_pre[:inflection])
                    lon_desc = np.array(lon_pre[:inflection])
                    surface_desc = np.array(surface_pre[:inflection])
                
                    ssha_desc = ssha_desc[np.argsort(-lat_desc)]
                    lon_desc = lon_desc[np.argsort(-lat_desc)]
                    surface_desc = surface_desc[np.argsort(-lat_desc)]
                    lat_desc = lat_desc[np.argsort(-lat_desc)]
                
                    ## Filter the track
                    input_ssh = open('../INPUT_ssh.dat', 'w')
                    for ilat in range(len(lat_desc)):
                        print(-lat_desc[ilat], ssha_desc[ilat], file=input_ssh)
                    input_ssh.close()

                    os.system('gmt filter1d ../INPUT_ssh.dat -Fg0.2 -D0.001 -fi0y -E > ../OUTPUT_ssh.dat')
                    os.system('rm ../INPUT_ssh.dat')
                
                    output_ssh = open('../OUTPUT_ssh.dat', 'r')
                    lat_desc_filt = []
                    ssha_desc_filt = []
                    for line in output_ssh:
                        line.strip()
                        columns = line.split()
                        lat_desc_filt.append(-float(columns[0]))
                        ssha_desc_filt.append(float(columns[1]))
                    output_ssh.close()
                
                    os.system('rm ../OUTPUT_ssh.dat')
                
                    #### Ascending ######
                
                    ssha_asc = np.array(ssha_pre[inflection:])
                    lat_asc = np.array(lat_pre[inflection:])
                    lon_asc = np.array(lon_pre[inflection:])
                    surface_asc = np.array(surface_pre[inflection:])
                
                    ssha_asc = ssha_asc[np.argsort(lat_asc)]
                    lon_asc = lon_asc[np.argsort(lat_asc)]
                    surface_asc = surface_asc[np.argsort(lat_asc)]
                    lat_asc = lat_asc[np.argsort(lat_asc)]
                
                    ## Filter the track
                    input_ssh = open('../INPUT_ssh.dat', 'w')
                    for ilat in range(len(lat_asc)):
                        print(lat_asc[ilat], ssha_asc[ilat], file=input_ssh)
                    input_ssh.close()

                    os.system('gmt filter1d ../INPUT_ssh.dat -Fg0.2 -D0.001 -fi0y -E > ../OUTPUT_ssh.dat')
                    os.system('rm ../INPUT_ssh.dat')
                
                    output_ssh = open('../OUTPUT_ssh.dat', 'r')
                    lat_asc_filt = []
                    ssha_asc_filt = []
                    for line in output_ssh:
                        line.strip()
                        columns = line.split()
                        lat_asc_filt.append(float(columns[0]))
                        ssha_asc_filt.append(float(columns[1]))
                    output_ssh.close()
                
                    os.system('rm ../OUTPUT_ssh.dat')

                    lat =  list(lat_desc_filt) + list(lat_asc_filt)
                    ssha = list(ssha_desc_filt) + list(ssha_asc_filt)
                    lon =  list(lon_desc) + list(lon_asc)
                    surface = list(surface_desc) + list(surface_asc)
                

                    if len(lat) == len(lon):
                        # Generate a list of retracker modes for this track
                        tracker_type = funct.mode_points(lat, lon, month)

                        # Find the boundaries
                        iedge_SAR_SARIn = []
                        for it in range(len(tracker_type)):
                            # Find retracker boundaries
                            if tracker_type[it:it + len_bound] == SAR_to_SARIn:
                                iedge_SAR_SARIn.append(it + len_bound//2)
                            elif tracker_type[it:it + len_bound] == SARIn_to_SAR:
                                iedge_SAR_SARIn.append(it + len_bound//2)

                        # For the SAR-SARIn boundary
                        for step in iedge_SAR_SARIn:
                            # If the boundary is ALL OCEAN
                            if surface[step - len_bound//2:step + len_bound//2] == [1] * len_bound:
                                # If it's a SAR to SARIn step
                                if tracker_type[step - len_bound//2:step + len_bound//2] == SAR_to_SARIn:
                                    if np.max(abs(np.gradient(lat[step - len_bound//2:step + len_bound//2]))) < 0.05:
                                        if abs(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2])) < .3:
                                            # Calculate circumpolar offset
                                            circum_offset_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                            hist_offset_circum_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                            # Choose what the sector the offset point lies within
                                            if -60. <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= 0.:
                                                #print('Weddell')
                                                offset_WEDD_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                                hist_offset_WEDD_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                            elif 0 <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= 160.:
                                                #print('Indian')
                                                offset_IND_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                                hist_offset_IND_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                            elif 160. <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= 180.:
                                                #print('Ross')
                                                offset_ROSS_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                                hist_offset_ROSS_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                            elif -180. <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= -130.:
                                                #print('Ross')
                                                offset_ROSS_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                                hist_offset_ROSS_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                            elif -130. <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= -60.:
                                                #print('Amundsen-Bellingshausen')
                                                offset_AMBEL_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))
                                                hist_offset_AMBEL_SAR_SARIn.append(np.mean(ssha[step - len_bound//2:step]) - np.mean(ssha[step:step + len_bound//2]))

                                # If it's a SARIn to SAR step
                                if tracker_type[step - len_bound//2:step + len_bound//2] == SARIn_to_SAR:
                                    if np.max(abs(np.gradient(lat[step - len_bound//2:step + len_bound//2]))) < 0.05:
                                        if abs(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step])) < .3:
                                            # Calculate circumpolar offset
                                            circum_offset_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                            hist_offset_circum_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                            # Choose what the sector the offset point lies within
                                            if -60. <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= 0.:
                                                #print('Weddell')
                                                offset_WEDD_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                                hist_offset_WEDD_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                            elif 0 <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= 160.:
                                                #print('Indian')
                                                offset_IND_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                                hist_offset_IND_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                            elif 160. <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= 180.:
                                                #print('Ross')
                                                offset_ROSS_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                                hist_offset_ROSS_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                            elif -180. <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= -130.:
                                                #print('Ross')
                                                offset_ROSS_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                                hist_offset_ROSS_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                            elif -130. <= np.mean(lon[step - len_bound//2:step + len_bound//2]) <= -60.:
                                                #print('Amundsen-Bellingshausen')
                                                offset_AMBEL_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))
                                                hist_offset_AMBEL_SAR_SARIn.append(np.mean(ssha[step:step + len_bound//2]) - np.mean(ssha[step - len_bound//2:step]))

            monthly_offset_WEDD_SAR_SARIn.append(np.mean(offset_WEDD_SAR_SARIn))
            monthly_offset_IND_SAR_SARIn.append(np.mean(offset_IND_SAR_SARIn))
            monthly_offset_ROSS_SAR_SARIn.append(np.mean(offset_ROSS_SAR_SARIn))  
            monthly_offset_AMBEL_SAR_SARIn.append(np.mean(offset_AMBEL_SAR_SARIn))
            monthly_offset_SAR_SARIn.append(np.mean(circum_offset_SAR_SARIn))

            WEDD_timeseries_SAR_SARIn.append(np.mean(offset_WEDD_SAR_SARIn))
            IND_timeseries_SAR_SARIn.append(np.mean(offset_IND_SAR_SARIn))
            ROSS_timeseries_SAR_SARIn.append(np.mean(offset_ROSS_SAR_SARIn)) 
            AMBEL_timeseries_SAR_SARIn.append(np.mean(offset_AMBEL_SAR_SARIn))
            timeseries_SAR_SARIn.append(np.mean(circum_offset_SAR_SARIn))
    
    pl.figure()
    pl.hist([hist_offset_WEDD_SAR_SARIn, hist_offset_IND_SAR_SARIn, hist_offset_ROSS_SAR_SARIn, hist_offset_AMBEL_SAR_SARIn], label=['Weddell', 'Indian', 'Ross', 'Amundsen-Bellingshausen'])
    pl.legend(loc='upper left')
    pl.title(year + ' LRM - SAR histogram')
    pl.xlabel('Offset Bin (m)')
    pl.ylabel('Frequency')
    pl.savefig('/Users/jmh2g09/Documents/PhD/Data/Offset/Figures/' + year + '_SAR_SARIn_offset_hist.png', format='png', doi=300, transparent=True, bbox_inches='tight')
    pl.close()

    A = range(np.min(month_number), np.max(month_number) + 1)
    pl.figure()
    pl.plot(A, monthly_offset_SAR_SARIn, label='Circumpolar', marker='.')
    pl.plot(A, monthly_offset_WEDD_SAR_SARIn, label='Weddell', marker='.')
    pl.plot(A, monthly_offset_IND_SAR_SARIn, label='Indian', marker='.')
    pl.plot(A, monthly_offset_ROSS_SAR_SARIn, label='Ross', marker='.')
    pl.plot(A, monthly_offset_AMBEL_SAR_SARIn, label='Amundsen-Bellingshausen', marker='.')
    pl.legend(loc='best')
    pl.title(year + ' SAR - SARIn (m) offset')
    pl.ylabel('Offset (m)')
    pl.xlabel('Month')
    pl.xlim([1, 12])
    pl.savefig('/Users/jmh2g09/Documents/PhD/Data/Offset/Figures/' + year + '_SAR_SARIn_offset_sectors.png', format='png', doi=300, transparent=True, bbox_inches='tight')
    pl.close()
    
    average_circumpolar_offset_SAR_SARIn += np.array(monthly_offset_SAR_SARIn)

f=open('/Users/jmh2g09/Documents/PhD/Data/Offset/SAR_SARIn_timeseries.txt', 'w')
for i in range(len(WEDD_timeseries_SAR_SARIn)):
    print(WEDD_timeseries_SAR_SARIn[i], IND_timeseries_SAR_SARIn[i], ROSS_timeseries_SAR_SARIn[i], AMBEL_timeseries_SAR_SARIn[i], timeseries_SAR_SARIn[i], file=f)
f.close()

fig = pl.figure()
pl.plot(dates, timeseries_SAR_SARIn, label='Circumpolar', marker='.')
pl.plot(dates, WEDD_timeseries_SAR_SARIn, label='Weddell', marker='.')
pl.plot(dates, IND_timeseries_SAR_SARIn, label='Indian', marker='.')
pl.plot(dates, ROSS_timeseries_SAR_SARIn, label='Ross', marker='.')
pl.plot(dates, AMBEL_timeseries_SAR_SARIn, label='Amundsen-Bellingshausen', marker='.')
pl.legend(loc='lower right', prop={'size':6})
fig.autofmt_xdate()
pl.ylabel('LRM - SAR$_\mathrm{ocean}$ offset (m)')
pl.savefig('/Users/jmh2g09/Documents/PhD/Data/Offset/Figures/SARSARIn_timeseries.png', format='png', doi=300, transparent=True, bbox_inches='tight')
pl.close()

average_circumpolar_offset_SAR_SARIn /= 6

print(average_circumpolar_offset_SAR_SARIn)

f = open('/Users/jmh2g09/Documents/PhD/Data/Offset/SAR-SARIn_offset.dat', 'w')
for mnth in range(len(average_circumpolar_offset_SAR_SARIn)):
    print(mnth + 1, average_circumpolar_offset_SAR_SARIn[mnth], file=f)

## Calculate the average offset for use as a constant (time) offset
constant_SAR_SARIn_offset = np.nanmean(timeseries_SAR_SARIn)
print(mnth + 2, constant_SAR_SARIn_offset, file=f)
f.close()

print('January SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[0])
print('Febuary SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[1])
print('March SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[2])
print('April SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[3])
print('May SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[4])
print('June SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[5])
print('July SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[6])
print('August SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[7])
print('September SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[8])
print('October SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[9])
print('November SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[10])
print('December SAR-SARIn offset: ', average_circumpolar_offset_SAR_SARIn[11])

print('Constant SAR-SARIn offset: ', constant_SAR_SARIn_offset)
