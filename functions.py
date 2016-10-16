import os
import numpy as np
from mpl_toolkits.basemap import Basemap
import decimal
import scipy.ndimage
from netCDF4 import Dataset
import matplotlib.pyplot as pl

def month_data(directory, month):
    """Extract latitude, longitude, sea surface height, surface ice concentration,
    and surface type data from all files in 'directory'.
    Also applies a retracker offset. See code for details."""
    files = os.listdir(directory)
    lat = []
    lon = []
    ssh = []
    ssh_2 = []
    type = []
    ice_conc = []
    for file in files:
        #print(file)
        lat_sub = []
        lon_sub = []
        ssh_sub = []
        ssh_2_sub = []
        type_sub = []
        ice_conc_sub = []
        lat_sub_asc = []
        lon_sub_asc = []
        ssh_sub_asc = []
        ssh_sub_2_asc = []
        type_sub_asc = []
        ice_conc_sub_asc = []
        lat_sub_desc = []
        lon_sub_desc = []
        ssh_sub_desc = []
        ssh_sub_2_desc = []
        ssh_filt_desc = []
        lat_sub_desc_new = []
        lon_sub_desc_new = []
        ssh_2_filt_desc = []
        type_sub_desc_new = []
        ice_conc_sub_desc_new = []
        ssh_2_filt_asc = []
        lon_sub_asc_new = []
        type_sub_asc_new = []
        ice_conc_sub_asc_new = []
        ssh_filt_asc = []
        lat_sub_asc_new = []
        type_sub_desc = []
        ice_conc_sub_desc = []
        f = open(file, 'r')
        for line in f:
            line = line.strip()
            columns = line.split()
            # If data point is listed as 'valid'
            if columns[1] == '1':
                # If data point is from open ocean (1) or from a lead (2)
                if columns[0] == '1' or columns[0] == '2':
                    # If the ssh is less than 3 m from the mean ssh
                    if abs(float(columns[7]) - float(columns[8])) <= 3.:
                        lat_sub.append(float(columns[5]))
                        lon_sub.append(float(columns[6]))
                        ice_conc_sub.append(float(columns[11]))
                        type_sub.append(float(columns[0]))
                        ssh_sub.append(float(columns[7]))
                        ssh_2_sub.append(float(columns[7]))
        
        # Identify the surface and tracker and apply the necessary offset
        # Generate a list of the retracker used at each point
        mode = mode_points(lat_sub, lon_sub, month)
        for point in range(len(mode)):
            # If the point is SAR and Ocean
            if mode[point] == 1 and type_sub[point] == 1:
                ssh_sub[point] += apply_offset(month, 'SAR_ocean')
            # If the point is SAR or SARIn and Lead
            elif (mode[point] == 1 or mode[point] == 2) and type_sub[point] == 2:
                ssh_sub[point] += apply_offset(month, 'ice')

        f.close()
        if len(lat_sub) > 3:
            # Do the DESCENDING tracks        
            descending = np.where(np.gradient(lat_sub) < 0.)[0]
            # If there are any descending tracks
            if len(descending) > 0.:
                ssh_sub_desc = ssh_sub[descending[0]:descending[-1]]
                ssh_sub_2_desc = ssh_2_sub[descending[0]:descending[-1]]
                lat_sub_desc = lat_sub[descending[0]:descending[-1]]
                lon_sub_desc = lon_sub[descending[0]:descending[-1]]
                ice_conc_sub_desc = ice_conc_sub[descending[0]:descending[-1]]
                type_sub_desc = type_sub[descending[0]:descending[-1]]
            
                bad_elements = []
                for issh in range(len(ssh_sub_desc)):
                    # If the value is greater than 3 std from the mean
                    if np.mean(ssh_sub_desc) - 3*np.std(ssh_sub_desc) > ssh_sub_desc[issh] > np.mean(ssh_sub_desc) + 3*np.std(ssh_sub_desc):
                        bad_elements.append(issh)
                for issh in range(len(ssh_sub_desc)-1):
                    # If the gradient between this point and the next point is greater than .5 m
                    if abs(ssh_sub_desc[issh] - ssh_sub_desc[issh + 1]) > .5:
                        bad_elements.append(issh + 1)
            
                # remove the points that meet the above criteria
                # In reverse order to avoid index problems
                for bad in sorted(np.unique(bad_elements), reverse=True):
                    del ssh_sub_desc[bad]
                    del ssh_sub_2_desc[bad]
                    del lat_sub_desc[bad]
                    del lon_sub_desc[bad]
                    del ice_conc_sub_desc[bad]
                    del type_sub_desc[bad]
                
                # Split the time series into two segments, where large gaps appear in the lat
                lat_grad = np.abs(np.gradient(lat_sub_desc))
                lat_grad_sort = sorted(lat_grad, reverse=True)
                
                #print('Descending gaps')
                threshold = np.where(lat_grad >= 0.4)[0]
                
                if len(threshold) > 1:
                    print(threshold)
                    grad = np.gradient(threshold)
                    print(grad)
                    
                    if np.logical_and(grad[0] == 1., grad[-1] > 1.):
                        threshold_2 = threshold[:-1]
                    elif np.logical_and(grad[0] > 1., grad[-1] == 1.):
                        threshold_2 = threshold[1:]
                    elif np.logical_and(grad[0] == 1., grad[-1] == 1.):
                        threshold_2 = threshold
                    elif np.logical_and(grad[0] > 1., grad[-1] > 1.):
                        threshold_2 = threshold
                    
                    #grad_2 = np.gradient(threshold_2)
                    
                    #if any(np.logical_and(grad_2[1:-1] >= 1., grad_2[1:-1] <= 5.)):
                        #threshold_3 = np.delete(threshold_2, np.where(np.logical_and(grad_2[1:-1] >= 1., grad_2[1:-1] <= 5.))[0] + 1)
                    #else:
                    #threshold_3 = threshold_2
                        
                    if len(threshold_2) % 2 != 0.:
                        if len(threshold_2) == 3.:
                            threshold_3 = list(np.delete(threshold_2, 1))
                        elif len(threshold_2) == 5.:
                            threshold_3 = list(np.delete(threshold_2, 2))

                        elif len(threshold_2) > 5:
                            
                            threshold_odd_beginning = threshold_2[:2]
                            threshold_odd_end = threshold_2[-2:]
                            
                            grad_odd = np.gradient(threshold_2[2:-2])
                            print(grad_odd)
                            if np.logical_and(grad_odd[0] == 1., grad_odd[-1] == 1.):
                                threshold_odd = np.delete(threshold_2[2:-2], 2)
                            elif np.logical_and(grad_odd[0] > 1., grad_odd[-1] == 1.):
                                threshold_odd = threshold_2[3:-2]
                            elif np.logical_and(grad_odd[0] == 1., grad_odd[-1] > 1.):
                                threshold_odd = threshold_2[2:-3]
                            elif np.logical_and(grad_odd[0] > 1., grad_odd[-1] > 1.):
                                print('Then we''re pretty fucked (Asc)')
                            
                            threshold_3 = list(threshold_odd_beginning) + list(threshold_odd) + list(threshold_odd_end)
                    else:
                        threshold_3 = threshold_2

                    print(threshold_3)
                    
                    if len(threshold_3) > 2:
                        arr = [[0, 0]]
                        for igap in range(0, len(threshold_3), 2):
                            arr.append([threshold_3[igap], threshold_3[igap + 1]])
                        arr.append([-1, -1])
                    else:
                        arr = [[0,0],[threshold_3[0], threshold_3[1]],[-1,-1]]
                
                    #pl.figure()
                    for iarr in range(np.shape(arr)[0] - 1):
                        cutoff_desc_1 = arr[iarr][1]
                        cutoff_desc_2 = arr[iarr + 1][0]
                
                        ssh_sub_desc_1 = ssh_sub_desc[cutoff_desc_1:cutoff_desc_2]
                        ssh_sub_2_desc_1 = ssh_sub_2_desc[cutoff_desc_1:cutoff_desc_2]
                        lat_sub_desc_1 = lat_sub_desc[cutoff_desc_1:cutoff_desc_2]
                        lon_sub_desc_1 = lon_sub_desc[cutoff_desc_1:cutoff_desc_2]
                        type_sub_desc_1 = type_sub_desc[cutoff_desc_1:cutoff_desc_2]
                        ice_conc_sub_desc_1 = ice_conc_sub_desc[cutoff_desc_1:cutoff_desc_2]
                        
                        #pl.plot(lat_sub_desc_1, ssh_sub_desc_1)
                                
                        # Apply a gaussian filter to the ssh data, with a 40 point (10 km) diameter
                        ssh_filt_desc_1 = list(scipy.ndimage.filters.gaussian_filter1d(ssh_sub_desc_1, 15., mode='nearest'))
                        ssh_filt_2_desc_1 = list(scipy.ndimage.filters.gaussian_filter1d(ssh_sub_2_desc_1, 15., mode='nearest'))
                            
                        ssh_filt_desc += ssh_filt_desc_1
                        ssh_2_filt_desc += ssh_filt_2_desc_1
                        lat_sub_desc_new += lat_sub_desc_1
                        lon_sub_desc_new += lon_sub_desc_1
                        type_sub_desc_new += type_sub_desc_1
                        ice_conc_sub_desc_new += ice_conc_sub_desc_1
                
                else:
                    ssh_filt_desc = list(scipy.ndimage.filters.gaussian_filter1d(ssh_sub_desc, 15., mode='nearest'))
                    ssh_2_filt_desc = list(scipy.ndimage.filters.gaussian_filter1d(ssh_sub_2_desc, 15., mode='nearest'))
                    lat_sub_desc_new = lat_sub_desc
                    lon_sub_desc_new = lon_sub_desc
                    type_sub_desc_new = type_sub_desc
                    ice_conc_sub_desc_new = ice_conc_sub_desc

                #pl.plot(lat_sub_desc_new, ssh_filt_desc, 'k')
                #pl.show()
                #pl.close()

                lat += lat_sub_desc_new
                lon += lon_sub_desc_new
                type += type_sub_desc_new
                ice_conc += ice_conc_sub_desc_new
                ssh += ssh_filt_desc
                ssh_2 += ssh_2_filt_desc

            ascending = np.where(np.gradient(lat_sub) > 0.)[0]
            # If there are any ascending tracks
            if len(ascending) > 0.:
                ssh_sub_asc = ssh_sub[ascending[1]:ascending[-1]]
                ssh_sub_2_asc = ssh_2_sub[ascending[1]:ascending[-1]]
                lat_sub_asc = lat_sub[ascending[1]:ascending[-1]]
                lon_sub_asc = lon_sub[ascending[1]:ascending[-1]]
                ice_conc_sub_asc = ice_conc_sub[ascending[1]:ascending[-1]]
                type_sub_asc = type_sub[ascending[1]:ascending[-1]]
        
                bad_elements = []
                # Do the Ascending tracks
                for issh in range(len(ssh_sub_asc)):
                    # If the value is greater than 3 std from the mean
                    if np.mean(ssh_sub_asc) - 3*np.std(ssh_sub_asc) > ssh_sub_asc[issh] > np.mean(ssh_sub_asc) + 3*np.std(ssh_sub_asc):
                        bad_elements.append(issh)
                for issh in range(len(ssh_sub_asc)-1):
                    # If the gradient between this point and the next point is greater than .5 m
                    if abs(ssh_sub_asc[issh] - ssh_sub_asc[issh + 1]) > .5:
                        bad_elements.append(issh + 1)
                
                for bad in sorted(np.unique(bad_elements), reverse=True):
                    del ssh_sub_asc[bad]
                    del ssh_sub_2_asc[bad]
                    del lat_sub_asc[bad]
                    del lon_sub_asc[bad]
                    del ice_conc_sub_asc[bad]
                    del type_sub_asc[bad]
                
                # Split the time series into two segments, where large gaps appear in the lat
                lat_grad = np.abs(np.gradient(lat_sub_asc))
                lat_grad_sort = sorted(lat_grad, reverse=True)
                
                #print('Ascending gaps')
                threshold = np.where(lat_grad >= 0.4)[0]
                
                if len(threshold) > 1:
                    print(threshold)
                    grad = np.gradient(threshold)
                    print(grad)
                    
                    if np.logical_and(grad[0] == 1., grad[-1] > 1.):
                        threshold_2 = threshold[:-1]
                    elif np.logical_and(grad[0] > 1., grad[-1] == 1.):
                        threshold_2 = threshold[1:]
                    elif np.logical_and(grad[0] == 1., grad[-1] == 1.):
                        threshold_2 = threshold
                    elif np.logical_and(grad[0] > 1., grad[-1] > 1.):
                        threshold_2 = threshold
                    else:
                        threshold_2 = threshold
                    
                    #grad_2 = np.gradient(threshold_2)
                    
                    #if any(np.logical_and(grad_2[1:-1] >= 1., grad_2[1:-1] <= 5.)):
                        #threshold_3 = np.delete(threshold_2, np.where(np.logical_and(grad_2[1:-1] >= 1., grad_2[1:-1] <= 5.))[0] + 1)
                    #else:
                    #threshold_3 = threshold_2
                        
                    if len(threshold_2) % 2 != 0.:
                        if len(threshold_2) == 3.:
                            threshold_3 = list(np.delete(threshold_2, 1))
                        elif len(threshold_2) == 5.:
                            threshold_3 = list(np.delete(threshold_2, 2))

                        elif len(threshold_2) > 5:
                            
                            threshold_odd_beginning = threshold_2[:2]
                            threshold_odd_end = threshold_2[-2:]
                            
                            grad_odd = np.gradient(threshold_2[2:-2])
                            print(grad_odd)
                            if np.logical_and(grad_odd[0] == 1., grad_odd[-1] == 1.):
                                threshold_odd = np.delete(threshold_2[2:-2], 2)
                            elif np.logical_and(grad_odd[0] > 1., grad_odd[-1] == 1.):
                                threshold_odd = threshold_2[3:-2]
                            elif np.logical_and(grad_odd[0] == 1., grad_odd[-1] > 1.):
                                threshold_odd = threshold_2[2:-3]
                            elif np.logical_and(grad_odd[0] > 1., grad_odd[-1] > 1.):
                                print('Then we''re pretty fucked (Asc)')
                            
                            threshold_3 = list(threshold_odd_beginning) + list(threshold_odd) + list(threshold_odd_end)
                    else:
                        threshold_3 = threshold_2

                    print(threshold_3)

                    if len(threshold_3) > 2:
                        arr = [[0, 0]]
                        for igap in range(0, len(threshold_3), 2):
                            arr.append([threshold_3[igap], threshold_3[igap + 1]])
                        arr.append([-1, -1])
                    else:
                        arr = [[0,0],[threshold_3[0], threshold_3[1]],[-1,-1]]
                
                    #pl.figure()
                    for iarr in range(np.shape(arr)[0] - 1):
                        cutoff_asc_1 = arr[iarr][1]
                        cutoff_asc_2 = arr[iarr + 1][0]

                        ssh_sub_asc_1 = ssh_sub_asc[cutoff_asc_1:cutoff_asc_2]
                        ssh_sub_2_asc_1 = ssh_sub_2_asc[cutoff_asc_1:cutoff_asc_2]
                        lat_sub_asc_1 = lat_sub_asc[cutoff_asc_1:cutoff_asc_2]
                        lon_sub_asc_1 = lon_sub_asc[cutoff_asc_1:cutoff_asc_2]
                        type_sub_asc_1 = type_sub_asc[cutoff_asc_1:cutoff_asc_2]
                        ice_conc_sub_asc_1 = ice_conc_sub_asc[cutoff_asc_1:cutoff_asc_2]
                    
                        #pl.plot(lat_sub_asc_1, ssh_sub_asc_1)
                                
                        # Apply a gaussian filter to the ssh data, with a 40 point (10 km) diameter
                        ssh_filt_asc_1 = list(scipy.ndimage.filters.gaussian_filter1d(ssh_sub_asc_1, 15., mode='nearest'))
                        ssh_filt_2_asc_1 = list(scipy.ndimage.filters.gaussian_filter1d(ssh_sub_2_asc_1, 15., mode='nearest'))
                        
                        ssh_filt_asc += ssh_filt_asc_1
                        ssh_2_filt_asc += ssh_filt_2_asc_1
                        lat_sub_asc_new += lat_sub_asc_1
                        lon_sub_asc_new += lon_sub_asc_1
                        type_sub_asc_new += type_sub_asc_1
                        ice_conc_sub_asc_new += ice_conc_sub_asc_1
                
                else:
                    ssh_filt_asc = list(scipy.ndimage.filters.gaussian_filter1d(ssh_sub_asc, 15., mode='nearest'))
                    ssh_2_filt_asc = list(scipy.ndimage.filters.gaussian_filter1d(ssh_sub_2_asc, 15., mode='nearest'))
                    lat_sub_asc_new = lat_sub_asc
                    lon_sub_asc_new = lon_sub_asc
                    type_sub_asc_new = type_sub_asc
                    ice_conc_sub_asc_new = ice_conc_sub_asc

                #pl.plot(lat_sub_asc_new, ssh_filt_asc, 'k')
                #pl.show()
                #pl.close()

                lat += lat_sub_asc_new
                lon += lon_sub_asc_new
                type += type_sub_asc_new
                ice_conc += ice_conc_sub_asc_new
                ssh += ssh_filt_asc
                ssh_2 += ssh_2_filt_asc

    return {'lat': lat, 'lon': lon, 'ssh': ssh, 'ssh_2': ssh_2, 'ice_conc': ice_conc, 'type': type}

def stereo(lat, lon):
    """Convert Lat and Lon (Polar) coordinates to stereographic (x, y) coordinates (km).
        Latitude in degrees.
        Longitude in degrees.
        sgn = 1 for Northern Hempsphere.
        sgn = -1 for Southern Hemisphere."""
    def general(angle):
        epsilon = 0.081816153  # Eccentricity of ellipsoid (Earth)
        T = (np.tan((np.pi/4) - (angle/2)) /
                ((1 - epsilon * np.sin(angle)) /
                    (1 + epsilon * np.sin(angle))) ** epsilon / 2)
        return T
    PHI = 70. * np.pi / 180  # Projection plane in radians (70 degrees)
    theta = np.absolute(lat) * np.pi / 180  # Latitude in radians
    phi = lon * (np.pi / 180)  # Longitude in radians
    epsilon = 0.081816153  # Eccentricity of ellipsoid (Earth)
    R = 6378.273  # Radius of ellipsoid in km (Earth)
    gamma = np.cos(PHI) / np.sqrt(1 - (epsilon**2) * np.sin(PHI)**2)
    rho = R * gamma * general(theta) / general(PHI)
    x = rho * np.sin(phi)  # stereographic x-coordinate in km
    y = rho * np. cos(phi)  # stereographic y-coordinate in km
    return {'X': x, 'Y': y}

def surface_area(lat, lon, cell_size_lat, cell_size_lon):
    """A function to calculate the surface area of a grid cell on a sphere.
        Grid cell has sides (cell_size_lat, cell_size_lon) in degrees.
        Returns the surface area of the grid cell at location (lat, lon) in km^2."""
    # Radius of the Earth (km)
    R = 6371.
    # Step 1, get limits of the grid cell in radians
    lat_side_min = (lat - (cell_size_lat / 2)) * np.pi / 180
    lat_side_max = (lat + (cell_size_lat / 2)) * np.pi / 180

    lon_side_min = (lon - (cell_size_lon / 2)) * np.pi / 180
    lon_side_max = (lon + (cell_size_lon / 2)) * np.pi / 180
    
    # Calculate the surface area of the cell
    S = (R**2)*(lon_side_max - lon_side_min)*(np.sin(lat_side_max) - np.sin(lat_side_min))
    
    return S

def grid05(data, lon_data, lat_data, lat_res, lon_res):
    """A function to grid lon, lat data.
    
    The data should be of the form (x, y, z), where x is the longitude, y is the latitude
    and z is the value at that position. data, lon_data, and lat_data must all have the  
    same length, and be one dimensional. res is the desired horizontal resolution, for example:
    for a 1-degree grid, use res = 1, for 0.5-degree grid, use res = 0.5.
    
    The gridded data is drawn on an equidistant cylindrical projection. Use your favourite
    projection conversion tool to convert the result to your desired projection.
    
    This simple function draws a square grid on top of the data distribution. Any data
    points that lie within a grid square are averaged and the number of data points
    averaged in that box is returned in xy_count."""
    
    m = Basemap(projection='cyl', llcrnrlat=-90, urcrnrlat=-30, llcrnrlon=-180,
                urcrnrlon=180, resolution='c')
    x_cyl, y_cyl = m(lon_data, lat_data)
    
    x_range = np.arange(np.round(np.min(x_cyl)), np.round(np.max(x_cyl))+ lon_res, lon_res)
    y_range = np.arange(np.round(np.min(y_cyl)), np.round(np.max(y_cyl))+ lat_res, lat_res)
    xy_grid = np.full([np.size(x_range), np.size(y_range)], fill_value=np.nan)
    xy_count = np.full([np.size(x_range), np.size(y_range)], fill_value=np.nan)

    for i in range(np.size(data)):
        x_coord = float(decimal.Decimal(float(x_cyl[i])).quantize(decimal.Decimal(str(lon_res)), rounding='ROUND_DOWN'))
        y_coord = float(decimal.Decimal(float(y_cyl[i])).quantize(decimal.Decimal(str(lat_res)), rounding='ROUND_DOWN'))

        ix_range = np.where(np.logical_and(x_range > x_coord - lon_res/2, x_range < x_coord + lon_res/2))
        iy_range = np.where(np.logical_and(y_range > y_coord - lat_res/2, y_range < y_coord + lat_res/2))

        if np.isnan(xy_grid[ix_range, iy_range]):
            xy_grid[ix_range, iy_range] = data[i]
            xy_count[ix_range, iy_range] = 1

        if not np.isnan(xy_grid[ix_range, iy_range]):
            xy_grid[ix_range, iy_range] = xy_grid[ix_range, iy_range] + data[i]
            xy_count[ix_range, iy_range] = xy_count[ix_range, iy_range] + 1

    xy_grid = xy_grid / xy_count

    return {'Grid':xy_grid, 'Count':xy_count, 'Lon':x_range, 'Lat':y_range}

def apply_offset(month, boundary):
    if boundary == 'SAR_ocean':
        if month == '01':
            return 0.005
        elif month == '02':
            return 0.007
        elif month == '03':
            return -0.009
        elif month == '04':
            return -0.018
        elif month == '05':
            return -0.010
        elif month == '06':
            return -0.019
        elif month == '07':
            return -0.030
        elif month == '08':
            return -0.022
        elif month == '09':
            return -0.016
        elif month == '10':
            return -0.017
        elif month == '11':
            return 0.001
        elif month == '12':
            return 0.012
    elif boundary == 'ice':
        if month == '01':
            return 0.052
        elif month == '02':
            return 0.044
        elif month == '03':
            return 0.034
        elif month == '04':
            return 0.043
        elif month == '05':
            return 0.047
        elif month == '06':
            return 0.065
        elif month == '07':
            return 0.075
        elif month == '08':
            return 0.075
        elif month == '09':
            return 0.068
        elif month == '10':
            return 0.072
        elif month == '11':
            return 0.050
        elif month == '12':
            return 0.050
#January LRM-SAR offset:  0.00489492491322
#Febuary LRM-SAR offset:  0.00688199790682
#March LRM-SAR offset:  -0.00897106525092
#April LRM-SAR offset:  -0.0181416179892
#May LRM-SAR offset:  -0.0101094678668
#June LRM-SAR offset:  -0.0187603584627
#July LRM-SAR offset:  -0.0295892239469
#August LRM-SAR offset:  -0.0219179266994
#September LRM-SAR offset:  -0.0162279361396
#October LRM-SAR offset:  -0.0174250239166
#November LRM-SAR offset:  0.00133077159719
#December LRM-SAR offset:  0.0124794197335

#January ocean-ice (SAR) offset:  0.0519413074729
#Febuary ocean-ice (SAR) offset:  0.0440994674621
#March ocean-ice (SAR) offset:  0.03386778963
#April ocean-ice (SAR) offset:  0.0432063759616
#May ocean-ice (SAR) offset:  0.0470435583904
#June ocean-ice (SAR) offset:  0.0645406477081
#July ocean-ice (SAR) offset:  0.0747555318892
#August ocean-ice (SAR) offset:  0.0745253922656
#September ocean-ice (SAR) offset:  0.0676124492288
#October ocean-ice (SAR) offset:  0.0723514436851
#November ocean-ice (SAR) offset:  0.0504626853533
#December ocean-ice (SAR) offset:  0.04950011136

def mode_points(lat, lon, month):
    '''Function that takes a list of lat and lon points and returns a list 
    corresponding to the SIRAL retracker mode with which that point was measured. 
    'month' is a string where '01' corresponds to January, '12' for December.
    
    Returns a list of length(lat) where the elements correspond to 
    Low Resolution Mode (0), SAR mode (1) or SARIn mode (2).'''
    
    def in_me(x, y, poly):
        '''Determine if a point is inside a given polygon or not
        Polygon is a list of (x,y) pairs.'''
    
        n = len(poly)
        inside = False

        p1x, p1y = poly[0]
        for i in range(n + 1):
            p2x,p2y = poly[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    # Load the polygon data
    nc = Dataset('/Users/jmh2g09/Documents/PhD/Data/Seperate Modes/Mode Mask/SARIn_polygon.nc', 'r')
    lat_poly_SARIn = nc.variables['Lat_SARIn'][:]
    lon_poly_SARIn = nc.variables['Lon_SARIn'][:]
    nc.close()
    nc = Dataset('/Users/jmh2g09/Documents/PhD/Data/Seperate Modes/Mode Mask/SAR_polygon.nc', 'r')
    lat_poly_SAR = nc.variables['Lat_SAR_' + month][:]
    lon_poly_SAR = nc.variables['Lon_SAR_' + month][:]
    nc.close()

    # Convert to polar stereographic x and y coordinates
    m = Basemap(projection='spstere', boundinglat=-50, lon_0=180, resolution='l')
    # For the SAR data
    stereo_x_SAR, stereo_y_SAR = m(lon_poly_SAR, lat_poly_SAR)
    polygon_SAR = list(zip(stereo_x_SAR, stereo_y_SAR))
    # For the SARIn data
    stereo_x_SARIn, stereo_y_SARIn = m(lon_poly_SARIn, lat_poly_SARIn)
    polygon_SARIn = list(zip(stereo_x_SARIn, stereo_y_SARIn))
    # For the track data
    stereo_x, stereo_y = m(lon, lat)

    xy_pair = list(zip(stereo_x, stereo_y))
    point_type = []
    for point in xy_pair:
        point_x = point[0]
        point_y = point[1]
        if in_me(point_x, point_y, polygon_SAR) == False and in_me(point_x, point_y, polygon_SARIn) == False:
            point_type.append(0)
        elif in_me(point_x, point_y, polygon_SAR) == True and in_me(point_x, point_y, polygon_SARIn) == False:
            point_type.append(1)
        elif in_me(point_x, point_y, polygon_SAR) == True and in_me(point_x, point_y, polygon_SARIn) == True:
            point_type.append(2)
    
    return point_type

def inpaint_nans(y):
    def nan_helper(y):
        """Helper to handle indices and logical indices of NaNs.

        Input:
            - y, 1d numpy array with possible NaNs
        Output:
            - nans, logical indices of NaNs
            - index, a function, with signature indices= index(logical_indices),
              to convert logical indices of NaNs to 'equivalent' indices
        Example:
            >>> # linear interpolation of NaNs
            >>> nans, x= nan_helper(y)
            >>> y[nans]= np.interp(x(nans), x(~nans), y[~nans])
        """

        return np.isnan(y), lambda z: z.nonzero()[0]
    nans, x= nan_helper(y)
    y[nans]= np.interp(x(nans), x(~nans), y[~nans])
    
    return y