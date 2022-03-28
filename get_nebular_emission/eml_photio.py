'''
# 4 arrays of random numbers: lines. File with 4 columns. Plot BPT to read and plot.
import numpy as np
import os
from matplotlib import pyplot as plt
from get_nebular_emission.eml_style import style1
import get_nebular_emission.eml_const as const
bpt_data = 'C:/Users/Olivia/PRUEBAS/bpt_data.dat' # r"example_data/bpt_data.dat"
header1 = 'line1   line2   line3   line4'

a = np.random.randint(1, 10, size=10)
b = np.random.randint(1, 10, size=10)
c = np.random.randint(1, 10, size=10)
d = np.random.randint(1, 10, size=10)

datatofile=np.column_stack((a, b, c, d))

with open(bpt_data,'w') as svfile:
    np.savetxt(svfile,datatofile,delimiter=' ',header=header1)
    svfile.closed
'''
import h5py
import numpy as np
from get_nebular_emission.eml_io import get_nheader, homedir, locate_interval
import get_nebular_emission.eml_const as const
from get_nebular_emission.eml_io import check_file
from pathlib import Path



# DICCIONARIO DE MODELOS DE PHOTOIO: Nombre del modelo y nombre del fichero con los límites
# Si lía mucho matriz de strings

mod_lim = {'gutkin16': r"nebular_data/gutkin_tables/limits_gutkin.txt"}
#mod_lim = {'gutkin16': 'C:/Users/Olivia/get_nebular_emission/nebular_data/gutkin_tables/limits_gutkin.txt'}
# mod_lim = {'gutkin16': [r"nebular_data/gutkin_tables/limits_gutkin.txt", 18}
# print(mod_lim.keys()) # To show the keys

#infile = r"nebular_data/gutkin_tables/nebular_emission_Z" + zname + ".txt"

def get_zfile(zmet_str, photmod='gutkin16'):

    '''
    Given a metallicity string get the name of the corresponding table

    Parameters
    ----------
    zmet_str : string
        Metallicity name in files
    photomod : string
        Name of the considered photoionisation model

    Returns
    -------
    zfile : string
        Name of the model file with data for the given metallicity
    '''

    root = 'nebular_data/' + photmod + '_tables/nebular_emission_Z'
    if len(zmet_str)<3:
        zmet_str = zmet_str+'0'
    zfile = root + zmet_str + '.txt'
    # Si son 2 numeros que le añada un cero
    file_fine = check_file(zfile)
    if (not file_fine):
        zfile = None

    return zfile


def get_limits(propname, photmod = 'gutkin16',verbose=True):
    '''
    Given a file with a structure: property + lower limit + upper limit,
    gets the limits of the parameters of the photoionization model.

    In the file we must find the properties well specified.
    The header lines have to start with '#'

    Parameters
    -------
    infile: string
        input file

    propname : string
        name of the property that we want

    Returns
    -------

    lower_limit: float
        lower limit of the requested property
    upper_limit: float
        upper limits of the requested property

    Examples
    -------
    infile:

    # Table 3 of Gutkin+2016 (https://arxiv.org/pdf/1607.06086.pdf)
    # Property      Lower_limit     Upper_limit
    Z               0.0001          0.040
    U               -4.0            -1.0
    xid             0.1             0.5
    nH               1               4


    >> get_limits(infile, propname = 'Z'):
        0.0001 0.04

    >> get_limits(infile, propname = 'nH'):
        1  4

    '''

    # HERE: Hacer otra función que lea los límites.
    # Como una iteración porque hay tres propiedades n_lim !! VER SLACK propname bucle
    # Si hay una n en la string se considera que son los límites de la n.
    # En esa función va a tomar logaritmos así está todo preparado.
    # Iteración sobre las tres propiedades de forma que solo tenga una cosa.

    try:
        infile = mod_lim[photmod]
    except KeyError:
        print('STOP (eml_photio): the {}'.format(photmod) + ' model is an unrecognised model in the dictionary mod_lim')
        print('                  Possible photmod= {}'.format(mod_lim.keys()))
        exit()

    # Check if the limits file exists:
    check_file(infile, verbose=verbose)
    print(infile)

    prop = np.loadtxt(infile,dtype=str,comments='#',usecols=(0),unpack=True)
    prop = prop.tolist()
    if propname not in prop:
        print('STOP (eml_photio): property {} '.format(propname)+'not found in the limits file {}'.format(infile))
        print('                   In the limits file we must find the properties written as: U, Z and nH')
        exit()
    else:
        ind = prop.index(propname)

        ih = get_nheader(infile,firstchar='#')
        lower_limit = np.loadtxt(infile, skiprows=ind+ih, max_rows=1, usecols=(1),unpack=True)
        upper_limit = np.loadtxt(infile,skiprows=ind+ih, max_rows=1,usecols=(2),unpack=True)
        return lower_limit,upper_limit

def clean_photarray(photmod='gutkin16', verbose=True):
    #clean_photarray(infile, in_Z, in_U, in_ne, photmod = 'gutkin16',verbose=True)
    #infile: siempre va a ser el que salga de eml_une, se podría poner el enlace y ya
    # lo que pasa es que solo tendríamos un archivo. Se podría introducir en el diccionario y así tener varios guardados
    # dependiendo del modelo. La idea además es que sea hdf5, siempre.
    #
    # in_Z, in_U, in_ne: Los nombres de las propiedades para buscarlas directamente en el archivo de límites. Siempre
    # van a ser las mismas columnas en el infile. Quizá ponerlo en un array: [Z, U, ne] = ['Z', 'U', 'nH']

    # No estoy teniendo en cuenta disco y bulbo: ¿Cómo hacer?
    # ¿Guardo en arrays loh12 = [disk, bulge], lu = [disk, bulge], lne = [disk, bulge]?

    '''
    Given a file with a structure: property + lower limit + upper limit,
    a file with the data, the name of the property that we want and its column in the file well specify,
    gets the array of the data property with the necessary changes due to the limits.


    Parameters
    ----------
    limfile: string
        file with the limits
    infile: string
        file with the data
    col_prop: float
        column of the property in the infile
    propname: string
        name of the property
    photmod:  string
        Model to get the luminosity lines for the interpolations
    verbose : boolean
        Yes = print out messages


    Returns
    -------
    prop : array
        array of the property choose with all the data in the limits.
    '''

    # Llama a la función que te dice los limites. Hacer otra función que limpie los límites.
    # Aqui poner un if que si el modelo es tal que haga tal cambio de unidades.
    # Para añadir un nuevo modelo, clean_photarray necesitará añadir cosas en el if respecto al cambio de unidades.
    # Aquí da array limpios, array 5 => array 5, con los elementos en los límites.



    # Read the data file:
    infile = r"output_data/U_ne_loh12.hdf5"

    check_file(infile, verbose=verbose)

    f = h5py.File(infile,'r')
    header = f['header']
    data = f['data']

    lu = data['lu'][:]
    lud=[]; lub=[]

    for ii, u in enumerate(lu):
        u1 = lu[ii]
        u1 = u1.tolist()
        lud.append(u1[0])
        lub.append((u1[1]))
    lud = np.array(lud)
    lub = np.array(lub)


    lne = data['lne'][:]
    lned=[];lneb=[]
    for ii, ne in enumerate(lne):
        ne1 = lne[ii]
        ne1 = ne1.tolist()
        lned.append(ne1[0])
        lneb.append((ne1[1]))
    lned = np.array(lned)
    lneb = np.array(lneb)


    loh12 = data['loh12'][:]
    loh12d=[];loh12b=[]
    for ii, oh12 in enumerate(loh12):
        oh121 = loh12[ii]
        oh121 = oh121.tolist()
        loh12d.append(oh121[0])
        loh12b.append((oh121[1]))
    loh12d = np.array(loh12d)
    loh12b = np.array(loh12b)


    lowerl, upperl = get_limits(propname='U', photmod=photmod)

    '''
    for ii, u in enumerate(lu):
        for iv in range(len(lu[ii])):
            ind = np.where(lu[ii,iv]>upperl)
            lu[ii, ind] = upperl
            ind = np.where(lu[ii,iv]<lowerl)
            lu[ii,ind] = lowerl
    print(lu)
    '''
    ind = np.where(lud > upperl)
    lud[ind] = upperl
    ind = np.where(lud < lowerl)
    lud[ind] = lowerl

    ind = np.where(lub > upperl)
    lub[ind] = upperl
    ind = np.where(lub < lowerl)
    lub[ind] = lowerl

    lu = np.stack((lud, lub))

    lowerl, upperl = get_limits(propname='nH', photmod=photmod)
    ind = np.where(lned > upperl)
    lned[ind] = upperl
    ind = np.where(lned < lowerl)
    lned[ind] = lowerl

    ind = np.where(lneb > upperl)
    lneb[ind] = upperl
    ind = np.where(lneb < lowerl)
    lneb[ind] = lowerl

    lne = np.stack((lned, lneb))

    lowerl, upperl = get_limits(propname='Z', photmod=photmod)
    ind = np.where(loh12d > upperl)
    loh12d[ind] = upperl
    ind = np.where(loh12d < lowerl)
    loh12d[ind] = lowerl

    ind = np.where(loh12b > upperl)
    loh12b[ind] = upperl
    ind = np.where(loh12b < lowerl)
    loh12b[ind] = lowerl

    loh12 = np.stack((loh12d, loh12b))

    return lu, lne, loh12
'''
    else:
        # Text file
        ih = get_nheader(infile)
        if ('.cvs' in infile):
            deli = ','
        else:
            deli = None

        
        prop = np.loadtxt(infile, delimiter=deli, skiprows=ih,usecols = col_prop, unpack=True)

    # Change of units
    #if photmod == 'Gutkin16':
     #   prop = np.log10(prop)  # Here: it works with nH but no with U, U is in log.
    # It must be consistent the limits.txt and the data.
'''



def get_lines_Gutkin(verbose=True):
    '''
    Given a file with the limits of the Gutkin model and a file with data,
    get 12+log(O/H), logU and logne to
    get the interpolations for the emission lines,
    using the tables
    from Gutkin et al. (2016) (https://arxiv.org/pdf/1607.06086.pdf)


    Parameters
    ----------
    infile: string
        file with the data
    photmods : string
      Model to go from U, Z and ne to emission lines luminosities.
    verbose : boolean
      Yes = print out messages

    Returns
    -------
    emission lines : floats
    '''
    zmet_str =['0001','0002','0005','001','002','004','006','008','010','014','017','020','030','040']
    zmets = np.full(len(zmet_str),const.notnum)
    zmets = np.array([float('0.' + zmet) for zmet in zmet_str])

    logubins = [-4., -3.5, -3., -2.5, -2., -1.5, -1.]

    nemline = 18
    #nemline_reduced = 4
    nzmet = 14
    nu = 7
    nzmet_reduced = 4
    zmets_reduced = np.array([0.0001, 0.002, 0.014, 0.030])

    emline_grid1 = np.zeros((nzmet_reduced,nu,nemline)) # From slower to faster
    emline_grid2 = np.zeros((nzmet,nu,nemline))
    emline_grid3 = np.zeros((nzmet,nu,nemline))
    emline_grid4 = np.zeros((nzmet_reduced,nu,nemline))

    l = 0
    kred = 0
    nn = 0

    for k, zname in enumerate(zmets):
        infile = get_zfile(zmet_str[k],photmod='gutkin')
        check_file(infile,verbose=True)
        #print(k,infile)
        ih = get_nheader(infile)

        with open(infile,'r') as ff:
            iline = -1.
            for line in ff:
                iline += 1

                if iline<ih:continue

                data = np.array((line.split()))
                lu = float(data[0])
                xid = float(data[1])
                nH = float(data[2])
                co = float(data[3])
                imf_cut = float(data[4])


                if xid==0.3 and co==1.and imf_cut==100:
                    if lu == -4.:
                        l = 0
                    if lu == -3.5:
                        l = 1
                    if lu == -3.:
                        l = 2
                    if lu == -2.5:
                        l = 3
                    if lu == -2.:
                        l = 4
                    if lu == -1.5:
                        l = 5
                    if lu == -1.:
                        l = 6


                    if nH==10 or nH==100 or nH==1000 or nH==10000:

                        if nH==10 or nH==10000:
                            if k==0:
                                kred = 0
                            if k==4:
                                kred = 1
                            if k==9:
                                kred = 2
                            if k==12:
                                kred = 3
                        for j in range(nemline):
                            if nH == 10:
                                emline_grid1[kred,l,j] = float(data[j+5]) #Revisar
                            if nH == 100:
                                emline_grid2[k,l,j] = float(data[j+5])
                            if nH == 1000:
                                emline_grid3[k,l,j] = float(data[j+5])
                            if nH == 10000:
                                emline_grid4[kred,l,j] = float(data[j+5])

    # Líneas de 201 a 212 no entiendo

    # log metallicity bins ready for interpolation:

    lzmets_reduced = np.full(len(zmets_reduced), const.notnum)
    ind = np.where(zmets_reduced > 0.)
    if (np.shape(ind)[1]) > 0:
        lzmets_reduced[ind] = np.log10(zmets_reduced[ind])


    lzmets = np.full(len(zmets), const.notnum)
    ind = np.where(zmets > 0.)
    if (np.shape(ind)[1] > 0):
        lzmets[ind] = np.log10(zmets[ind])

    #print(lzmets,lzmets_reduced)

    # now read GAlFORM output
    file = r"output_data/output_kashino20.hdf5"
    check_file(file,verbose=True)

    f = h5py.File(file, 'r')
    header = f['header']
    data = f['data']

    lu = data['lu'][:]
    lud = []; lub = []

    for ii, u in enumerate(lu):
        u1 = lu[ii]
        u1 = u1.tolist()
        lud.append(u1[0])
        lub.append((u1[1]))
    ndat = len(lud)  # 203436
    lud = np.array(lud)
    lub = np.array(lub)

    lne = data['lne'][:]
    lned = []; lneb = []
    for ii, ne in enumerate(lne):
        ne1 = lne[ii]
        ne1 = ne1.tolist()
        lned.append(ne1[0])
        lneb.append((ne1[1]))
    lned = np.array(lned)
    lneb = np.array(lneb)


    loh12 = data['loh12'][:] - const.ohsun
    loh12d = []; loh12b = []
    for ii, oh12 in enumerate(loh12):
        oh121 = loh12[ii]
        oh121 = oh121.tolist()
        loh12d.append(oh121[0])
        loh12b.append((oh121[1]))
    loh12d = np.array(loh12d)
    loh12b = np.array(loh12b)

    # Close the output file
    f.close()

    # Interpolate in all three ne grids to start with u-grid first, since the same for all grids

    # DISK
    emline_int1 = np.zeros((nemline,ndat))
    emline_int2 = np.zeros((nemline, ndat))
    emline_int3 = np.zeros((nemline, ndat))
    emline_int4 = np.zeros((nemline, ndat))

    nebline_disk = np.zeros((nemline,ndat))

    # Interpolate over disk ionisation parameter
    du = []
    j = []
    for logud in lud:
        j1 = locate_interval(logud,logubins)
        if j1 == 0:
            du.append(0.0)
            j.append(0)
            #du = 0.0
            j1 = 0
        elif j1 == nu - 1:
            du.append(1.0)
            j.append(nu-2)
            #du = 1.0
            j1 = nu - 2
        else:
            d = (logud - logubins[j1]) / (logubins[j1 + 1] - logubins[j1])
            du.append(d)
            j.append(j1)
    #print(j, len(j))

    # Interpolate over disk gas metallicity loh12d
    dz = []
    i = []
    for logzd in loh12d:
        i1 = locate_interval(logzd,lzmets_reduced)

        if i1==0:
            dz.append(0.0)
            #dz = 0.0
            i1 = 0
            i.append(0)
        elif i1 == nzmet_reduced-1:
            dz.append(1.0)
            #dz = 1.0
            i1 = nzmet_reduced-2
            i.append(nzmet_reduced-2)
        else:
            d = (logzd - lzmets_reduced[i1])/(lzmets_reduced[i1+1]-lzmets_reduced[i1])
            dz.append(d)
            i.append(i1)

    for k in range(nemline):
        for ii in range(ndat):
            #emline_grid1 = np.zeros((nzmet_reduced, nu, nemline))
            #print(emline_grid1[i[ii]][j[ii]][k])
            emline_int1[k][ii] = (1.-dz[ii])*(1.-du[ii])*emline_grid1[i[ii]][j[ii]][k]+\
                                 dz[ii]*(1-du[ii])*emline_grid1[i[ii]+1][j[ii]][k]+\
                                 (1.-dz[ii])*du[ii]*emline_grid1[i[ii]][j[ii]+1][k]+\
                                 dz[ii]*du[ii]*emline_grid1[i[ii]+1][j[ii]+1][k]

            emline_int4[k][ii] = (1.-dz[ii])*(1.-du[ii])*emline_grid4[i[ii]][j[ii]][k]+\
                                 dz[ii]*(1-du[ii])*emline_grid4[i[ii]+1][j[ii]][k]+\
                                 (1.-dz[ii])*du[ii]*emline_grid4[i[ii]][j[ii]+1][k]+\
                                 dz[ii]*du[ii]*emline_grid4[i[ii]+1][j[ii]+1][k]


    # full metallicity grid for emlines_grid2 ne=100 and emlines_grid3 ne=1000

    dz = []
    i = []
    for logzd in loh12d:
        i1 = locate_interval(logzd, lzmets)

        if i1 == 0:
            dz.append(0.0)
            # dz = 0.0
            i1 = 0
            i.append(0)
        elif i1 == nzmet - 1:
            dz.append(1.0)
            # dz = 1.0
            i1 = nzmet - 2
            i.append(nzmet - 2)
        else:
            d = (logzd - lzmets[i1]) / (lzmets[i1 + 1] - lzmets[i1])
            dz.append(d)
            i.append(i1)

    for k in range(nemline):
        for ii in range(ndat):
            emline_int2[k][ii] = (1.-dz[ii])*(1.-du[ii])*emline_grid2[i[ii]][j[ii]][k]+\
                                 dz[ii]*(1-du[ii])*emline_grid2[i[ii]+1][j[ii]][k]+\
                                 (1.-dz[ii])*du[ii]*emline_grid2[i[ii]][j[ii]+1][k]+\
                                 dz[ii]*du[ii]*emline_grid2[i[ii]+1][j[ii]+1][k]

            emline_int3[k][ii] = (1.-dz[ii])*(1.-du[ii])*emline_grid3[i[ii]][j[ii]][k]+\
                                 dz[ii]*(1-du[ii])*emline_grid3[i[ii]+1][j[ii]][k]+\
                                 (1.-dz[ii])*du[ii]*emline_grid3[i[ii]][j[ii]+1][k]+\
                                 dz[ii]*du[ii]*emline_grid3[i[ii]+1][j[ii]+1][k]

    # Interpolate over ne
    # use gas density in disk logned
    for n in range(ndat):
        if (lned[n] > 2. and lned[n] <= 3.):
            dn = (lned[n] -2.)/(3. - 2.)
            for k in range(nemline):
                nebline_disk[k][n] = (1.-dn)*emline_int2[k][n] + (dn)*emline_int3[k][n]

        elif (lned[n] > 1. and lned[n] <= 2.):
            dn = (lned[n] -1.)/(2. - 1.)
            for k in range(nemline):
                nebline_disk[k][n] = (1.-dn)*emline_int1[k][n] + (dn)*emline_int2[k][n]

        elif (lned[n] > 3. and lned[n]<=4.):
            dn = (lneb[n] - 3.)/(4. - 3.)
            for k in range(nemline):
                nebline_disk[k][n] = (1. - dn) * emline_int3[k][n] + (dn) * emline_int4[k][n]
            print('hay mayor que 3')

        elif (lned[n] <= 1.):
            for k in range(nemline):
                nebline_disk[k][n] = emline_int1[k][n]
        elif (lned[n] > 4.):
            for k in range(nemline):
                nebline_disk[k][n] = emline_int4[k][n]
        else:
            print('log(ne)disk out of limits','log(ne)disk = {}'.format(lned[n]))

    # repeat interpolation for bulge if there is an ongoing burst
    # HERE: check if there is an ongoing bulge with the masses

    #BURST
    # Interpolate over bulge ionisation parameter
    emline_int1 = np.zeros((nemline,ndat))
    emline_int2 = np.zeros((nemline, ndat))
    emline_int3 = np.zeros((nemline, ndat))
    emline_int4 = np.zeros((nemline, ndat))

    nebline_bulge = np.zeros((nemline,ndat))

    # Interpolate over disk ionisation parameter
    du = []
    j = []
    for logub in lub:
        j1 = locate_interval(logub,logubins)
        if j1 == 0:
            du.append(0.0)
            j.append(0)
            #du = 0.0
            j1 = 0
        elif j1 == nu - 1:
            du.append(1.0)
            j.append(nu-2)
            #du = 1.0
            j1 = nu - 2
        else:
            d = (logub - logubins[j1]) / (logubins[j1 + 1] - logubins[j1])
            du.append(d)
            j.append(j1)
    #print(j, len(j))

    # Interpolate over disk gas metallicity loh12d
    dz = []
    i = []
    for logzb in loh12b:
        i1 = locate_interval(logzb,lzmets_reduced)

        if i1==0:
            dz.append(0.0)
            #dz = 0.0
            i1 = 0
            i.append(0)
        elif i1 == nzmet_reduced-1:
            dz.append(1.0)
            #dz = 1.0
            i1 = nzmet_reduced-2
            i.append(nzmet_reduced-2)
        else:
            d = (logzb - lzmets_reduced[i1])/(lzmets_reduced[i1+1]-lzmets_reduced[i1])
            dz.append(d)
            i.append(i1)

    for k in range(nemline):
        for ii in range(ndat):
            #emline_grid1 = np.zeros((nzmet_reduced, nu, nemline))
            #print(emline_grid1[i[ii]][j[ii]][k])
            emline_int1[k][ii] = (1.-dz[ii])*(1.-du[ii])*emline_grid1[i[ii]][j[ii]][k]+\
                                 dz[ii]*(1-du[ii])*emline_grid1[i[ii]+1][j[ii]][k]+\
                                 (1.-dz[ii])*du[ii]*emline_grid1[i[ii]][j[ii]+1][k]+\
                                 dz[ii]*du[ii]*emline_grid1[i[ii]+1][j[ii]+1][k]

            emline_int4[k][ii] = (1.-dz[ii])*(1.-du[ii])*emline_grid4[i[ii]][j[ii]][k]+\
                                 dz[ii]*(1-du[ii])*emline_grid4[i[ii]+1][j[ii]][k]+\
                                 (1.-dz[ii])*du[ii]*emline_grid4[i[ii]][j[ii]+1][k]+\
                                 dz[ii]*du[ii]*emline_grid4[i[ii]+1][j[ii]+1][k]


    # full metallicity grid for emlines_grid2 ne=100 and emlines_grid3 ne=1000

    dz = []
    i = []
    for logzb in loh12b:
        i1 = locate_interval(logzb, lzmets)

        if i1 == 0:
            dz.append(0.0)
            # dz = 0.0
            i1 = 0
            i.append(0)
        elif i1 == nzmet - 1:
            dz.append(1.0)
            # dz = 1.0
            i1 = nzmet - 2
            i.append(nzmet - 2)
        else:
            d = (logzb - lzmets[i1]) / (lzmets[i1 + 1] - lzmets[i1])
            dz.append(d)
            i.append(i1)

    for k in range(nemline):
        for ii in range(ndat):
            emline_int2[k][ii] = (1.-dz[ii])*(1.-du[ii])*emline_grid2[i[ii]][j[ii]][k]+\
                                 dz[ii]*(1-du[ii])*emline_grid2[i[ii]+1][j[ii]][k]+\
                                 (1.-dz[ii])*du[ii]*emline_grid2[i[ii]][j[ii]+1][k]+\
                                 dz[ii]*du[ii]*emline_grid2[i[ii]+1][j[ii]+1][k]

            emline_int3[k][ii] = (1.-dz[ii])*(1.-du[ii])*emline_grid3[i[ii]][j[ii]][k]+\
                                 dz[ii]*(1-du[ii])*emline_grid3[i[ii]+1][j[ii]][k]+\
                                 (1.-dz[ii])*du[ii]*emline_grid3[i[ii]][j[ii]+1][k]+\
                                 dz[ii]*du[ii]*emline_grid3[i[ii]+1][j[ii]+1][k]

    # Interpolate over ne
    # use gas density in disk logned
    for n in range(ndat):
        if (lneb[n] > 2. and lneb[n] <= 3.):
            dn = (lneb[n] -2.)/(3. - 2.)
            for k in range(nemline):
                nebline_bulge[k][n] = (1.-dn)*emline_int2[k][n] + (dn)*emline_int3[k][n]

        elif (lneb[n] > 1. and lneb[n] <= 2.):
            dn = (lneb[n] - 1.)/(2. - 1.)
            for k in range(nemline):
                nebline_bulge[k][n] = (1.-dn)*emline_int1[k][n] + (dn)*emline_int2[k][n]

        elif (lneb[n] > 3. and lneb[n]<=4.):
            dn = (lneb[n] - 3.)/(4. - 3.)
            for k in range(nemline):
                nebline_bulge[k][n] = (1. - dn) * emline_int3[k][n] + (dn) * emline_int4[k][n]
            print('hay mayor que 3')
        elif (lneb[n] <= 1.): #Use grid 1
            for k in range(nemline):
                nebline_bulge[k][n] = emline_int1[k][n]
        elif (lneb[n] > 4.):
            for k in range(nemline): #Use grid 4
                nebline_bulge[k][n] = emline_int4[k][n]
            print('hay mayor que 4')
        else:
            print('log(ne)bulge out of limits','log(ne)bulge = {}'.format(lneb[n]))

    f = h5py.File(file,'a')

    hfdat = f['data']
    hfdat.create_dataset('nebline_disk', data = nebline_disk)
    hfdat['nebline_disk'].dims[0].label = 'disk lines units: [3.826E+33egr s^-1 per unit SFR(Mo/yr) for 10^8yr]'
    hfdat.create_dataset('nebline_bulge', data = nebline_bulge)
    hfdat['nebline_bulge'].dims[0].label = 'burst lines units: [3.826E+33egr s^-1 per unit SFR(Mo/yr) for 10^8yr]'
    f.close()
    lines = 'interpolations done'


    return lines


def get_lines(infile, photmod='Gutkin16',verbose=False, Testing=False, Plotting=False):
    #(in_loh12, in_lu, in_lne, photmods='Gutkin16', verbose=False, Testing=False, Plotting=False):
    '''
    Given 12+log(O/H), logU and logne,
    get the interpolations for the emission lines

    Parameters
    ----------
    infile: string
        file with the data
    photmods : string
      Model to go from U, Z and ne to emission lines luminosities.
    verbose : boolean
      Yes = print out messages
    Plotting : boolean
      If True run verification plots with all data.
    Testing : boolean
      Yes = to only run over few entries for testing purposes

    Returns
    -------
      emission lines : floats
    '''

    # Hacer un loop sobre las tres arrays y que te las limpie el código.
    # loh12 = clean_photarrray(in_loh12=,photmod=,prop=loh12) Hacer para los tres

    if (photmod == 'Gutkin16'):
        lines = get_lines_Gutkin(infile, verbose=verbose)
    else:
        print('STOP (eml_photio): Unrecognised model to get emission lines.')
        print('                Possible photmod= {}'.format(const.photmods))
        exit()


    return lines





#if __name__== "__main__":
    #print(Path.home())
    #print(get_lines_Gutkin(verbose=True))
    #print(get_limits(propname='U',photmod='gutkin16',verbose=True))
    #print(mod_lim)