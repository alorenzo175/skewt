from numpy import ma,array,linspace,log,cos,sin,pi,zeros,exp,arange,trapz
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
from matplotlib.ticker import FixedLocator, AutoLocator, ScalarFormatter
import matplotlib.transforms as transforms
import matplotlib.axis as maxis
import matplotlib.artist as artist
from matplotlib.projections import register_projection
from matplotlib.pyplot import rcParams,figure,show,draw
from matplotlib.ticker import MultipleLocator, FormatStrFormatter


from skewt.thermodynamics import VirtualTemp,Latentc,SatVap,MixRatio,GammaW,\
    VirtualTempFromMixR,MixR2VaporPress,DewPoint,Theta,TempK,Density,DensityHumid
from skewt.thermodynamics import Rs_da, Cp_da, Epsilon,degCtoK


from UserDict import UserDict
from datetime import datetime
import os,sys
import warnings


class SkewXTick(maxis.XTick):
    #Copyright (c) 2008 Ryan May
    def draw(self, renderer):
        if not self.get_visible(): 
            return
        renderer.open_group(self.__name__)

        if self.gridOn:
            self.gridline.draw(renderer)
        if self.tick1On:
            self.tick1line.draw(renderer)
        if self.tick2On:
            self.tick2line.draw(renderer)

        if self.label1On:
            self.label1.draw(renderer)
        if self.label2On:
            self.label2.draw(renderer)

        renderer.close_group(self.__name__)

    def set_clip_path(self, clippath, transform=None):
        artist.Artist.set_clip_path(self, clippath, transform)
        self.tick1line.set_clip_path(clippath, transform)
        self.tick2line.set_clip_path(clippath, transform)
        self.gridline.set_clip_path(clippath, transform)
    
    set_clip_path.__doc__ = artist.Artist.set_clip_path.__doc__

class SkewXAxis(maxis.XAxis):
    #Copyright (c) 2008 Ryan May
    def _get_tick(self, major):
        return SkewXTick(self.axes, 0, '', major=major)

    def draw(self, renderer, *args, **kwargs):
        'Draw the axis lines, grid lines, tick lines and labels'
        ticklabelBoxes = []
        ticklabelBoxes2 = []

        if not self.get_visible(): 
            return
        renderer.open_group(__name__)
        interval = self.get_view_interval()
        for tick, loc, label in self.iter_ticks():
            if tick is None: 
                continue
            if transforms.interval_contains(interval, loc):
                tick.set_label1(label)
                tick.set_label2(label)
            tick.update_position(loc)
            tick.draw(renderer)
            if tick.label1On and tick.label1.get_visible():
                extent = tick.label1.get_window_extent(renderer)
                ticklabelBoxes.append(extent)
            if tick.label2On and tick.label2.get_visible():
                extent = tick.label2.get_window_extent(renderer)
                ticklabelBoxes2.append(extent)

        # scale up the axis label box to also find the neighbors, not
        # just the tick labels that actually overlap note we need a
        # *copy* of the axis label box because we don't wan't to scale
        # the actual bbox

        self._update_label_position(ticklabelBoxes, ticklabelBoxes2)

        self.label.draw(renderer)

        self._update_offset_text_position(ticklabelBoxes, ticklabelBoxes2)
        self.offsetText.set_text( self.major.formatter.get_offset() )
        self.offsetText.draw(renderer)

class SkewXAxes(Axes):
    #Copyright (c) 2008 Ryan May
    # The projection must specify a name.  This will be used be the
    # user to select the projection, i.e. ``subplot(111,
    # projection='skewx')``.
    name = 'skewx'

    def _init_axis(self):
        #Taken from Axes and modified to use our modified X-axis
        "move this out of __init__ because non-separable axes don't use it"
        self.xaxis = SkewXAxis(self)
        self.yaxis = maxis.YAxis(self)
        self._update_transScale()

    def draw(self, *args):
        '''
        draw() is overridden here to allow the data transform to be updated
        before calling the Axes.draw() method.  This allows resizes to be
        properly handled without registering callbacks.  The amount of
        work done here is kept to a minimum.
        '''
        self._update_data_transform()
        Axes.draw(self, *args)

    def _update_data_transform(self):
        '''
        This separates out the creating of the data transform so that
        it alone is updated at draw time.
        '''
        # This transforms x in pixel space to be x + the offset in y from
        # the lower left corner - producing an x-axis sloped 45 degrees
        # down, or x-axis grid lines sloped 45 degrees to the right
        self.transProjection.set(transforms.Affine2D(\
                array([[1, 1, -self.bbox.ymin], [0, 1, 0], [0, 0, 1]])))

        # Full data transform
        self.transData.set(self._transDataNonskew + self.transProjection)

    def _set_lim_and_transforms(self):
        """
        This is called once when the plot is created to set up all the
        transforms for the data, text and grids.
        """
        #Get the standard transform setup from the Axes base class
        Axes._set_lim_and_transforms(self)

        #Save the unskewed data transform for our own use when regenerating
        #the data transform. The user might want this as well
        self._transDataNonskew = self.transData

        #Create a wrapper for the data transform, so that any object that
        #grabs this transform will see an updated version when we change it
        self.transData = transforms.TransformWrapper(
            transforms.IdentityTransform())

        #Create a wrapper for the proj. transform, so that any object that
        #grabs this transform will see an updated version when we change it
        self.transProjection = transforms.TransformWrapper(
            transforms.IdentityTransform())
        self._update_data_transform()

    def get_xaxis_transform(self, which='grid'):
        """
        Get the transformation used for drawing x-axis labels, ticks
        and gridlines.  The x-direction is in data coordinates and the
        y-direction is in axis coordinates.

        We override here so that the x-axis gridlines get properly
        transformed for the skewed plot.
        """
        return self._xaxis_transform + self.transProjection

    # Disable panning until we find a way to handle the problem with
    # the projection
    def start_pan(self, x, y, button):
        pass

    def end_pan(self):
        pass

    def drag_pan(self, button, key, x, y):
        pass

    def other_housekeeping(self,pmin=100.,mixratio=array([])):
        # Added by Thomas Chubb
        self.yaxis.grid(True,ls='-',color='y',lw=0.5)

        # Plot x-grid lines instead of using xaxis.grid().
        # This is because xaxis.grid only plots skew lines 
        # that intersect the lower x axis... a possible fix
        # would be to use twinx() to plot upper and lower
        # grid lines but I think that's messy too.
        for TT in linspace(-100,100,21):
            self.plot([TT,TT],[1050,pmin],color='y',lw=0.5)

        # self.set_ylabel('Pressure (hPa)')
        self.set_xlabel('Temperature (C)')
        self.set_yticks(linspace(100,1000,10))
        self.yaxis.set_major_formatter(ScalarFormatter())
        self.set_xlim(-40,30)
        self.set_ylim(1050.,pmin)
        self.spines['right'].set_visible(False)
        self.get_yaxis().set_tick_params(which="both",size=0)
        self.get_xaxis().set_tick_params(which="both",size=0)

    def set_xticklocs(self,xticklocs):
        # Added by Thomas Chubb
        self.set_xticks(xticklocs)

    def add_dry_adiabats(self,T0,P,do_labels=True,**kwargs):
        # Added by Thomas Chubb
        P0=1000.
        T=array([ (st+degCtoK)*(P/P0)**(Rs_da/Cp_da)-degCtoK for st in T0 ])
        labelt=[ (st+degCtoK)*1**(Rs_da/Cp_da) for st in T0 ]
        if kwargs.has_key('color'): 
            col=kwargs['color']
        else: 
            col='k'
        for tt,ll in zip(T,labelt):
            self.plot(tt,P,**kwargs)
            if do_labels:
                if (tt[8]>-50) and (tt[8]<20):
                    self.text(tt[8],P[8]+10,'%d'%(ll),fontsize=8,\
                            ha='center',va='bottom',rotation=-30,color=col,\
                            bbox={'facecolor':'w','edgecolor':'w'})
        return T
    

    def add_moist_adiabats(self,T0,P,do_labels=True,**kwargs):
        # Added by Thomas Chubb
        T=array([lift_wet(st,P) for st in T0])
        if kwargs.has_key('color'): 
            col=kwargs['color']
        else: 
            col='k'
        for tt in T:
            self.plot(tt,P,**kwargs)
            # if (tt[-1]>-60) and (tt[-1]<-10):
            if do_labels:
                self.text(tt[-1],P[-1],'%d'%tt[0],ha='center',va='bottom',\
                        fontsize=8, bbox={'facecolor':'w','edgecolor':'w'},color=col)

    def add_mixratio_isopleths(self,w,P,do_labels=True,**kwargs):
        # Added by Thomas Chubb
        e=array([P*ww/(.622+ww) for ww in w])
        T = 243.5/(17.67/log(e/6.112) - 1)
        if kwargs.has_key('color'): 
            col=kwargs['color']
        else: 
            col='k'

        for tt,mr in zip(T,w):
            self.plot(tt,P.flatten(),**kwargs)
            if do_labels:
                if (tt[-1]>-45) and (tt[-1]<20):
                    if mr*1000<1.:
                        fmt="%4.1f"
                    else:
                        fmt="%d"
                    self.text(tt[-1],P[-1],fmt%(mr*1000),\
                            color=col, fontsize=8,ha='center',va='bottom',\
                            bbox={'facecolor':'w','edgecolor':'w'})

# Now register the projection with matplotlib so the user can select
# it.
register_projection(SkewXAxes)

class Sounding(UserDict):
    # Copyright (c) 2013 Thomas Chubb 
    """Utilities to read, write and plot sounding data quickly and without fuss
    
    INPUTS:
    filename:   If creating a sounding from a file, the full file name. The 
        format of this file is quite pedantic and needs to conform 
        to the format given by the University of Wyoming soundings 
        (see weather.uwyo.edu/upperair/sounding.html) 
    data:   Soundings can be made from atmospheric data. This should be 
        in the form of a python dict with (at minimum) the following 
        fields:

        TEMP: dry-bulb temperature (Deg C)
        DWPT: dew point temperature (Deg C)
        PRES: pressure (hPa)
        SKNT: wind speed (knots)
        WDIR: wind direction (deg)

        The following fields are also used, but not required by the 
        plot_skewt routine:

        HGHT (m)
        RELH (%)
        MIXR (g/kg)
        THTA (K)
        THTE (K)
        THTV (K)
    """


    def __init__(self,filename=None,data=None):
        UserDict.__init__(self)

        if data is None:
            self.data={}
            self.uwyofile(filename)
        else:
            self.data=data
            if not data.has_key("SoundingDate"):
                self["SoundingDate"]="(no date)"
            if not data.has_key("StationNumber"):
                self["StationNumber"]="(no number)"

    def plot_skewt(self, imagename=None, title=None, fig=None, **kwargs):
        """A wrapper for plotting the skewt diagram for a Sounding instance."""
        
        self.make_skewt_axes(fig=fig)
        self.add_profile(**kwargs)
        try:
            parcel=self.surface_parcel()
            self.lift_parcel(*parcel)
        except KeyError as e:
            warnings.warn('%s' % e)
        try:
            self.column_diagnostics()
        except KeyError as e:
            warnings.warn('%s' % e)

        if isinstance(title, str):
            self.skewxaxis.set_title(title)
        else:
            self.skewxaxis.set_title("%s %s"%(self["StationNumber"],self['SoundingDate']))

        if imagename is not None:
            self.fig.savefig(imagename,dpi=100)

    def add_points(self, xpoints, ypoints, **kwargs):
        if 'marker' in kwargs:
            marker = kwargs.pop('marker')
        else:
            marker = 'o'

        if 'color' in kwargs:
            color = kwargs.pop('color')
        else:
            color = 'red'

        if 'zorder' in kwargs:
            zorder = kwargs.pop('zorder')
        else:
            zorder = 10

        self.skewxaxis.plot(xpoints, ypoints, marker=marker, color=color, 
                            zorder=zorder, **kwargs)
        return self.fig


    def add_profile(self,**kwargs):
        """Add a new profile to the SkewT plot.

        This is abstracted from plot_skewt to enable the plotting of
        multiple profiles on a single axis, by updating the data attribute.
        For example:
        >>>
        S=SkewT.Sounding(data={})
        S.make_skewt_axes()
        S.uwyofile("../examples/94975.2013062800.txt")
        S.add_profile(color="b",bloc=0.5)
        S.uwyofile("../examples/94975.2013070900.txt")
        S.add_profile(color="r",bloc=1.)
        >>>
        Use the kwarg 'bloc' to set the alignment of the wind barbs from 
        the centerline (useful if plotting multiple profiles on the one axis)
        >>>
        Modified 25/07/2013: enforce masking of input data for this 
        function (does not affect the data attribute).
        """

        # I must be a dummy because I can't make 
        # this work any other way!!
        if kwargs.has_key('bloc'):
            bloc=kwargs.pop('bloc')
        else:
            bloc=0.5

        try: 
            pres = ma.masked_invalid(self.data['pres'])
        except KeyError: 
            raise KeyError, "Pres in hPa (PRES) is required!"

        try: 
            tc=ma.masked_invalid(self.data['temp'])
        except KeyError: 
            raise KeyError, "Temperature in C (TEMP) is required!"

        try: 
            dwpt=ma.masked_invalid(self.data['dwpt'])
        except KeyError:
            warnings.warn("Warning: No DWPT available")
            dwpt=ma.masked_array(zeros(pres.shape),mask=True)
            

        try:
            sknt=self.data['sknt']
            drct=self.data['drct']
            rdir = (270.-drct)*(pi/180.)
            uu = ma.masked_invalid(sknt*cos(rdir))
            vv = ma.masked_invalid(sknt*sin(rdir))
        except KeyError:
            warnings.warn("Warning: No SKNT/DRCT available")
            uu=ma.masked_array(zeros(pres.shape),mask=True)
            vv=ma.masked_array(zeros(pres.shape),mask=True)

        tcprof=self.skewxaxis.plot(tc, pres, zorder=5,**kwargs)
        dpprof=self.skewxaxis.plot(dwpt, pres, zorder=5,**kwargs)

        # this line should no longer cause an exception
        nbarbs=(~uu.mask).sum()

        skip=max(1,int(nbarbs/32))

        if kwargs.has_key('color'): 
            bcol=kwargs['color']
        else: 
            bcol='k'

        if kwargs.has_key('alpha'): 
            balph=kwargs['alpha']
        else: 
            balph=1.

        self.wbax.barbs((zeros(pres.shape)+bloc)[::skip]-0.5, pres[::skip],\
                uu[::skip], vv[::skip],\
                length=6,color=bcol,alpha=balph,lw=0.5)

        self.skewxaxis.other_housekeeping()

        return tcprof

    def init_profile_plot(self, fig=None, **kwargs):
        if 'marker' in kwargs:
            marker = kwargs.pop('marker')
        else:
            marker = 'o'

        if 'color' in kwargs:
            color = kwargs.pop('color')
        else:
            color = 'red'

        if 'zorder' in kwargs:
            zorder = kwargs.pop('zorder')
        else:
            zorder = 10

        self.make_skewt_axes(fig=fig)
        self.wind_pts = self.skewxaxis.plot([],[], marker=marker, color=color, 
                                            zorder=zorder, **kwargs)[0]
        self.plt_title = self.skewxaxis.set_title('')
        self.tcprof_line = self.skewxaxis.plot([],[], zorder=5,**kwargs)[0]
        self.dpprof_line = self.skewxaxis.plot([],[], zorder=5,**kwargs)[0]

        return self.tcprof_line,self.dpprof_line,self.plt_title,self.wind_pts

    def set_profile_data(self, pts=[[],[]]):
        try: 
            pres = ma.masked_invalid(self.data['pres'])
        except KeyError: 
            raise KeyError, "Pres in hPa (PRES) is required!"

        try: 
            tc=ma.masked_invalid(self.data['temp'])
        except KeyError: 
            raise KeyError, "Temperature in C (TEMP) is required!"

        try: 
            dwpt=ma.masked_invalid(self.data['dwpt'])
        except KeyError:
            warnings.warn("Warning: No DWPT available")
            dwpt=ma.masked_array(zeros(pres.shape),mask=True)
            

        try:
            sknt=self.data['sknt']
            drct=self.data['drct']
            rdir = (270.-drct)*(pi/180.)
            uu = (sknt*cos(rdir))
            vv = (sknt*sin(rdir))
        except KeyError:
            warnings.warn("Warning: No SKNT/DRCT available")
            uu=zeros(pres.shape)
            vv=zeros(pres.shape)

        self.tcprof_line.set_data(tc, pres)
        self.dpprof_line.set_data(dwpt, pres)
        self.plt_title.set_text("%s %s"%(self["StationNumber"],self['SoundingDate']))
        self.wind_pts.set_data(*zip(*pts))

        return self.tcprof_line,self.dpprof_line,self.plt_title,self.wind_pts


    def make_skewt_axes(self,pmax=1050.,pmin=100., fig=None):
        """Set up the skew-t axis the way I like to see it"""
        
        if fig is None:
            self.fig = figure(figsize=(8,8))
        else:
            self.fig = fig
        self.fig.clf()
        rcParams.update({\
            'font.size':10,\
            })

        self.skewxaxis=self.fig.add_axes([.065,.1,.71,.8], projection='skewx')
        self.skewxaxis.set_yscale('log')

        xticklocs=arange(-80,45,10)
        T0 = xticklocs

        P=linspace(pmax,pmin,37)

        w = array([0.0001,0.0004,0.001, 0.002, 0.004, 0.007, 0.01, 0.016, 0.024, 0.032])
        self.skewxaxis.add_mixratio_isopleths(w,P[P>=700],color='g',ls='--',alpha=1.,lw=0.5)
        self.skewxaxis.add_dry_adiabats(linspace(250,440,20)-degCtoK,P,color='g',ls='--',alpha=1.,lw=0.5)
        self.skewxaxis.add_moist_adiabats(linspace(8,32,7),P[P>=200],color='g',ls='--',alpha=1.,lw=0.5)

        self.skewxaxis.set_title("%s %s"%(self["StationNumber"],self['SoundingDate']))
        self.skewxaxis.other_housekeeping()

        self.wbax=self.fig.add_axes([0.685,0.1,0.1,0.8],sharey=self.skewxaxis,frameon=False)
        self.wbax.xaxis.set_ticks([],[])
        self.wbax.yaxis.grid(True,ls='-',color='y',lw=0.5)
        for tick in self.wbax.yaxis.get_major_ticks():
            # tick.label1On = False
            pass
        self.wbax.get_yaxis().set_tick_params(size=0,color='y')
        self.wbax.set_xlim(-1.5,1.5)
        self.wbax.get_yaxis().set_visible(False)

        # Set up standard atmosphere height scale on 
        # LHS of plot. 
        majorLocatorKM   = MultipleLocator(2)
        majorLocatorKFT  = MultipleLocator(5)
        minorLocator     = MultipleLocator(1)

        self.kmhax=self.fig.add_axes([0.775,0.1,1e-6,0.8],frameon=True)
        self.kmhax.xaxis.set_ticks([],[])
        self.kmhax.spines['left'].set_color('k')
        self.kmhax.spines['right'].set_visible(False)
        self.kmhax.tick_params(axis='y', colors='k',labelsize=8)
        self.kmhax.set_ylim(0,16.18)
        self.kmhax.set_title("km/kft",fontsize=10)
        self.kmhax.get_yaxis().set_tick_params(which="both",direction='out')
        self.kmhax.yaxis.set_major_locator(majorLocatorKM)
        self.kmhax.yaxis.set_minor_locator(minorLocator)

        self.fthax=self.kmhax.twinx()
        self.fthax.xaxis.set_ticks([],[])
        self.fthax.tick_params(axis='y', colors='k',labelsize=8)
        self.fthax.set_ylim(0,53.084)
        self.fthax.get_yaxis().set_tick_params(which="both",direction='out')
        self.fthax.yaxis.set_major_locator(majorLocatorKFT)
        self.fthax.yaxis.set_minor_locator(minorLocator)
        return self.skewxaxis,self.wbax

    def uwyofile(self,fname):
        """Reads the raw profile data from a Universiy of Wyoming sounding file.

        This is the primary method of IO for SkewT. The University of 
        Wyoming maintains a nice database of global upper air data which is
        kept up-to-date. Given a filename, this method updates the sounding 
        data with the text data in the file.

        NOTES
        1. The input file has to conform *Exactly* to the University of 
           Wyoming file format. This is because I look for data fields at 
           specific places on each line.
        2. I ignore the diagnostics at the end of the file, because the idea 
           is to calculate these myself.
        """
        #--------------------------------------------------------------------
        # This *should* be a convenient way to read a uwyo sounding
        #--------------------------------------------------------------------
        fid=open(fname)
        lines=fid.readlines()
        nlines=len(lines)

        lhi=[1, 9,16,23,30,37,46,53,58,65,72]
        rhi=[7,14,21,28,35,42,49,56,63,70,77]


        # initialise output data structure
        output={}

        fields=lines[3].split()
        units=lines[4].split()

        # Handle the file header
        # First line for WRF profiles differs from the UWYO soundings
        header=lines[0]
        if header[:5]=='00000':
            # WRF profile
            self['StationNumber']='00000'
            self['Longitude']=float(header.split()[5].strip(","))
            self['Latitude']=float(header.split()[6])
            self['SoundingDate']=header.split()[-1]
        else:
            self['StationNumber']=header[:5]
            dstr=(' ').join(header.split()[-4:])
            self['SoundingDate']=datetime.strptime(dstr,"%HZ %d %b %Y").strftime("%Y-%m-%d_%H:%M:%S") 

        # This is a data pre-initialisation step. I have used the number of lines minus the number
        # of lines of diagnostics.
        for ff in fields:
            # output[ff.lower()]=zeros((nlines-34))-999.
            output[ff.lower()]=[]

        lcounter=5
        for line,idx in zip(lines[6:],range(nlines)):
            lcounter+=1
            ### Version < 0.1.4
            # try: output[fields[0].lower()][idx]=float(line[lhi[0]:rhi[0]])
            # except ValueError: break

            ### New code. We test for pressure in the first column. 
            ### If there's no pressure, we get out!
            try: 
                output[fields[0].lower()].append(float(line[lhi[0]:rhi[0]]))
            except ValueError: 
                break
            
            for ii in range(1,len(rhi)):
                try: 
                    # Debug only:
                    # print fields[ii].lower(), float(line[lhi[ii]:rhi[ii]].strip())
                    ### Version < 0.1.4
                    # output[fields[ii].lower()][idx]=float(line[lhi[ii]:rhi[ii]].strip())
                     
                    ### New Code. Append to list instead of indexing 
                    ### pre-allocated data. Explicitly allocate -999
                    ### for invalid data (catch ValueError)
                    textdata=line[lhi[ii]:rhi[ii]].strip()
                    output[fields[ii].lower()].append(float(textdata))
                except ValueError: 
                    output[fields[ii].lower()].append(-999.)

        for field in fields:
            ff=field.lower()
            # set mask for missing data
            self.data[ff]=ma.masked_values(output[ff],-999.)

        return None

    def column_diagnostics(self):
        """Wrapper for column diagnostics"""

        self["Diagnostics"]={}
        dtext ="Column:\n"

        self["Diagnostics"]["TPW"]=self.precipitable_water()
        dtext+="%s: %5.2fmm"%("TPW", self["Diagnostics"]["TPW"])

        self.fig.text(0.825,0.750,dtext,fontname="monospace",va='top')

    def precipitable_water(self):
        """Calculate Total Precipitable Water (TPW) for sounding.

        TPW is defined as the total column-integrated water vapour. I
        calculate it from the dew point temperature because this is the
        fundamental moisture variable in this module (even though it is RH 
        that is usually measured directly)
        """

        tempk=self['temp']+degCtoK
        prespa=self['pres']*100.
        hghtm=self['hght']

        # Get Water Vapour Mixing Ratio, by calculation
        # from dew point temperature
        try:
            dwptc=self['dwpt']
        except KeyError:
            warnings.warn( "Warning: No MIXR or DWPT for TPW calculation")
            return -999.
        vprespa=SatVap(dwptc)
        mixrkg=MixRatio(vprespa,prespa)

        # Calculate density of air (accounting for moisture)
        rho=DensityHumid(tempk,prespa,vprespa)

        # Trapezoidal rule to approximate TPW (units kg/m^2==mm)
        tpw=trapz(mixrkg*rho,hghtm)

        return tpw

    def lift_parcel(self,startp,startt,startdp):
        """Lift a parcel to discover certain properties.
        
        
        INPUTS:
        startp:  Pressure (hPa)
        startt:  Temperature (C)
        startdp: Dew Point Temperature (C)
        """
        from numpy import interp

        try:
            assert startt>startdp
        except AssertionError:
            warnings.warn("Warning: Not a valid parcel. Check Td<Tc")
            return

        Pres=linspace(startp,100,100)

        # Lift the dry parcel
        T_dry=(startt+degCtoK)*(Pres/startp)**(Rs_da/Cp_da)-degCtoK 

        # Mixing ratio isopleth
        starte=SatVap(startdp)
        startw=MixRatio(starte,startp*100)
        e=Pres*startw/(.622+startw)
        T_iso=243.5/(17.67/log(e/6.112)-1)

        # Solve for the intersection of these lines (LCL).
        # interp requires the x argument (argument 2)
        # to be ascending in order!
        P_lcl=interp(0,T_iso-T_dry,Pres)
        T_lcl=interp(P_lcl,Pres[::-1],T_dry[::-1])

        col=[.6,.6,.6]

        # zorder
        zo=4

        # Plot traces below LCL
        self.skewxaxis.plot(T_dry[Pres>=P_lcl],Pres[Pres>=P_lcl],color=col,lw=2,zorder=zo)
        self.skewxaxis.plot(T_iso[Pres>=P_lcl],Pres[Pres>=P_lcl],color=col,lw=2,zorder=zo)
        self.skewxaxis.plot(T_lcl,P_lcl,ls='',marker='o',mec=col,mfc=col,zorder=zo)

        # Now lift a wet parcel from the intersection point
        preswet=linspace(P_lcl,200)
        tempwet=lift_wet(T_lcl,preswet)

        # Plot trace above LCL
        self.skewxaxis.plot(tempwet,preswet,color=col,lw=2,zorder=zo)

        # Add text to sounding
        dtext ="Parcel:\n"
        dtext+="Ps:  %6.1fhPa\n"%startp
        dtext+="TCs:   %4.1fC\n"%startt
        dtext+="TDs:   %4.1fC\n"%startdp
        dtext+="Plcl:%6.1fhPa\n"%P_lcl
        dtext+="Tlcl:  %4.1fC"%T_lcl

        self["Parcel"]={\
                "Ps":startp,\
                "TCs":startt,\
                "TDs":startdp,\
                "Plcl":P_lcl,\
                "Tlcl":T_lcl}


        self.fig.text(0.825,0.895,dtext,fontname="monospace",va='top')

        return

    def surface_parcel(self,mixdepth=125):
        """Returns parameters for a parcel initialised by:
        1. Surface pressure (i.e. pressure of lowest level)
        2. Surface temperature determined from max(theta) of lowest <mixdepth> mbar
        3. Dew point temperature representative of lowest <mixdepth> mbar

        Inputs:
        mixdepth (mbar): depth to average mixing ratio over
        """

        pres=self.data["pres"]
        temp=self.data["temp"]
        try:
            dwpt=self.data["dwpt"]
        except KeyError:
            warnings.warn("Unable to calculate surface parcel characteristics without dwpt")
            return (pres[0], temp[0], 1e20)

        # identify the layers for averaging
        layers=pres>pres[0]-mixdepth
        
        # parcel pressure is surface pressure
        pres_s=pres[0]

        # average theta over mixheight to give
        # parcel temperature
        thta_mix=Theta(temp[layers]+degCtoK,pres[layers]*100.).max()
        temp_s=TempK(thta_mix,pres_s*100)-degCtoK

        # average mixing ratio over mixheight
        vpres=SatVap(dwpt)
        mixr=MixRatio(vpres,pres*100)
        mixr_mix=mixr[layers].mean()
        vpres_s=MixR2VaporPress(mixr_mix,pres_s*100)

        # surface dew point temp
        dwpt_s=DewPoint(vpres_s)

        return pres_s,temp_s,dwpt_s

def lift_wet(startt,pres):
    #--------------------------------------------------------------------
    # Lift a parcel moist adiabatically from startp to endp.
    # Init temp is startt in C, pressure levels are in hPa    
    #--------------------------------------------------------------------

    temp=startt
    t_out=zeros(pres.shape);t_out[0]=startt
    for ii in range(pres.shape[0]-1):
        delp=pres[ii]-pres[ii+1]
        temp=temp-100*delp*GammaW(temp+degCtoK,(pres[ii]-delp/2)*100)
        t_out[ii+1]=temp

    return t_out





if __name__=='__main__':

    if len(sys.argv)==1 or sys.argv[1]=="example":
        # Do the examples in the "examples" directory
        examples=("2013070200","2013070900",)
        parcels=((1004.,17.4,8.6),(1033.,10.7,-0.9),)
        for ex,pc in zip(examples,parcels):
            sounding=Sounding("../examples/94975.%s.txt"%ex)
            sounding.make_skewt_axes()
            sounding.add_profile(color='r',lw=2)
            sounding.lift_parcel(*pc)
            sounding.column_diagnostics()
            sounding.fig.savefig("../examples/94975.%s.png"%ex)
    else:
        sounding=Sounding(sys.argv[1])
        sounding.plot_skewt(color='r')
    
    show()

    

