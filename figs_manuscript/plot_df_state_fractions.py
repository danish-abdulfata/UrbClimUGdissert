import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

fontsize = 9
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams.update({'font.size': fontsize})
mpl.rcParams['legend.numpoints'] = 1
from matplotlib.patches import Patch


import warnings
warnings.filterwarnings("ignore")

#fn_dir = "/data/"
fn_dir = "/"

# Urban description experiments
sim_codes = ['2_1b', '2_2a', '2_2b']
sim_codes_clean = ['sLC', 'LCZ', 'uLC']
show_case_city='NL-Amsterdam'

# sites
site_list = pd.read_csv('resources/sitelist_urbanplumber.csv')
sites = list(site_list['sitename'].values);
#sites = ['AU-Preston']

# Create folder to store tmp figures
#figdir = Path("/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data/figs")
figdir = Path("/home/demuzmp4/Dropbox/Apps/Overleaf/Demuzere_etal_supy-lcz (1)/figs")
figdir.mkdir(parents=True, exist_ok=True)

# Read in the surface fraction data
sfr_class = {
    'Paved': '#d0d0d0',
    'Buildings': '#AA4A44',
    'Eve. Trees': '#355E3B',
    'Dec. Trees': '#228B22',
    'Grass': '#cfe4c2',
    'Bare Soil': '#eed9ae',
    'Water': '#a9c8e3',
}

def plot_sfr_individual_site(site, fontsize):

    # Plot the surface cover fractions as stacked bars, for one site
    fig, ax = plt.subplots(1, 1, figsize=(5,5))

    sfr_arr = np.zeros((len(sim_codes), len(sfr_class)))
    pd_list = []
    th_list = []

    for i, sim_code in enumerate(sim_codes):
        fn_state = os.path.join(
            fn_dir,
            'data',
            site,
            f"output/buffer/df_state_{sim_code}.pkl"
        )
        df_state = pd.read_pickle(fn_state)
        sfr_arr[i, :] = df_state['sfr_surf'].values
        pd_list.append(np.round(df_state['popdensdaytime'].values.flatten()[0],1))
        #popden_arr[i, :2] = df_state['popdensdaytime'].values
        #popden_arr[i, 2] = df_state['popdensnighttime'].values
        th_list.append(np.round(float(df_state['evetreeh'].values),1)) # Same for 'dectreeh'

    df_sfr_arr = pd.DataFrame(sfr_arr)
    df_sfr_arr.index = sim_codes_clean
    df_sfr_arr.columns = list(sfr_class.keys())

    df_sfr_arr.plot(kind='bar', stacked=True, rot=0,
                         xlabel='LC category', ylabel='Surface fraction [-]',
                         color=list(sfr_class.values()),
                         ax=ax)
    # Add actual values to bars
    for c in ax.containers:
        # Optional: if the segment is small or 0, customize the labels
        labels = [np.round(v.get_height(),2) if v.get_height() > 0.025 else '' for v in c]

        # remove the labels parameter if it's not needed for customized labels
        ax.bar_label(c, labels=labels, label_type='center')

    # Legend: https://stackoverflow.com/questions/4700614/how-to-put-the-legend-outside-the-plot
    # Shrink current axis's height by 10% on the bottom
    # Shrink current axis by 20%
    box = ax.get_position()
    ax.set_position([box.x0, box.y0, box.width * 1, box.height])

    # Put a legend to the right of the current axis
    ax.legend(loc='lower left', bbox_to_anchor=(1.0, -0.02))

    # Add tree height and popden
    ax2 = ax.twiny()
    ax2_posx = ax.get_xticks()
    #ax2.set_xticks(ax2_posx)
    ax2.set_xticks([])
    ax2.set_xticklabels([])
    ax2.set_xbound(ax.get_xbound())

    pd_list[1] = '-'
    for i in range(3):
        # ax2.text(-0.4,1.07,'PopDensity', ha='right')
        # ax2.text(ax2_posx[i],1.07, pd_list[i], fontsize=fontsize, ha='center')
        # ax2.text(-0.4, 1.11, 'TreeHeight', ha='right')
        # ax2.text(ax2_posx[i], 1.11, th_list[i], fontsize=fontsize, ha='center')
        ax2.text(ax2_posx[i], 1.07, f"{pd_list[i]} | {th_list[i]}",
                 fontsize=fontsize, ha='center')

    # Add title, with site name
    #ax.set_title(site, fontsize=fontsize)
    ax.set_title(site, fontsize=fontsize + 1, pad=15, fontweight="bold")

    # Clean up
    plt.tight_layout()

    # Save
    FIG_FILE = os.path.join(
        figdir,
        f"df_state_sfr_surf_{site}.pdf"
    )
    plt.savefig(FIG_FILE, dpi=300)
    plt.close(fig)

    print(f"Figure available at: {FIG_FILE}")

plot_sfr_individual_site(show_case_city, fontsize)



def plot_sfr_all_sites(sites, fontsize):

    # Plot the surface cover fractions as stacked bars, for one site
    fig, axs = plt.subplots(5, 4, figsize=(10,11), sharex=True, sharey=True)
    ax = axs.flatten()

    for s_i, site in enumerate(sites):

        if s_i == 20:
            legend_on = True
        else:
            legend_on = False

        sfr_arr = np.zeros((len(sim_codes), len(sfr_class)))
        pd_list = []
        th_list = []

        for i, sim_code in enumerate(sim_codes):
            fn_state = os.path.join(
                fn_dir,
                'data',
                site,
                f"output/buffer/df_state_{sim_code}.pkl"
            )
            df_state = pd.read_pickle(fn_state)
            sfr_arr[i, :] = df_state['sfr_surf'].values
            pd_list.append(np.round(df_state['popdensdaytime'].values.flatten()[0],1))
            #popden_arr[i, :2] = df_state['popdensdaytime'].values
            #popden_arr[i, 2] = df_state['popdensnighttime'].values
            th_list.append(np.round(float(df_state['evetreeh'].values),1)) # Same for 'dectreeh'

        df_sfr_arr = pd.DataFrame(sfr_arr)
        df_sfr_arr.index = sim_codes_clean
        df_sfr_arr.columns = list(sfr_class.keys())

        l1 = df_sfr_arr.plot(kind='bar', stacked=True, rot=0,
                        xlabel='LC category', ylabel='Surface fraction [-]',
                        color=list(sfr_class.values()),
                        legend=legend_on,
                        ax=ax[s_i])
        # Add actual values to bars
        for c in ax[s_i].containers:
            # Optional: if the segment is small or 0, customize the labels
            labels = [np.round(v.get_height(),2) if v.get_height() > 0.05 else '' for v in c]

            # remove the labels parameter if it's not needed for customized labels
            ax[s_i].bar_label(c, labels=labels, label_type='center')

        # Add tree height and popden
        ax2 = ax[s_i].twiny()
        ax2_posx = ax[s_i].get_xticks()
        #ax2.set_xticks(ax2_posx)
        ax2.set_xticks([])
        ax2.set_xticklabels([])
        ax2.set_xbound(ax[s_i].get_xbound())

        pd_list[1] = '-'
        for i in range(3):
            # ax2.text(-0.4,1.07,'PopDensity', ha='right')
            # ax2.text(ax2_posx[i],1.07, pd_list[i], fontsize=fontsize, ha='center')
            # ax2.text(-0.4, 1.11, 'TreeHeight', ha='right')
            # ax2.text(ax2_posx[i], 1.11, th_list[i], fontsize=fontsize, ha='center')
            ax2.text(ax2_posx[i], 1.07, f"{pd_list[i]} | {th_list[i]}",
                     fontsize=fontsize, ha='center')

        # Add title, with site name
        ax[s_i].set_title(site, fontsize=fontsize+1, pad=15, fontweight="bold")

    # Legend: https://stackoverflow.com/questions/9834452/how-do-i-make-a-single-legend-for-many-subplots
    handles, labels = ax[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=len(sfr_class.keys()),
               loc='lower center', bbox_to_anchor=(0, 0, 1, 1),
               bbox_transform=plt.gcf().transFigure
    )

    # Clean up
    fig.tight_layout(rect=(0,0.02,1,1))

    # Save
    FIG_FILE = os.path.join(
        figdir,
        f"df_state_sfr_surf_allsites.pdf"
    )
    plt.savefig(FIG_FILE, dpi=300)
    plt.close(fig)

    print(f"Figure available at: {FIG_FILE}")


sites_1 = sites.remove(show_case_city) # remove show-case site
plot_sfr_all_sites(sites_1, fontsize)


def create_table_sfr_all_sites(sites, sim_codes):

    # Initialize dataframe
    iterables = [sites, sim_codes]
    df_index = pd.MultiIndex.from_product(iterables, names=["site", "experiment"])
    df = pd.DataFrame(
        index=df_index,
        columns = list(sfr_class.keys()) + ['PopDen', 'TH'])

    for site in sites:

        for sim_code in sim_codes:

            # Read state
            fn_state = os.path.join(
                fn_dir,
                'data',
                site,
                f"output/buffer/df_state_{sim_code}.pkl"
            )
            df_state = pd.read_pickle(fn_state)
            df.loc[(site, sim_code)][:7] = df_state['sfr_surf'].values.flatten()

            # Population
            df.loc[(site, sim_code), 'PopDen'] = np.round(df_state['popdensdaytime'].values.flatten()[0],1)

            # Tree height
            df.loc[(site, sim_code), 'TH'] = np.round(float(df_state['evetreeh'].values),1)

    # Save
    TABLE_FILE = os.path.join(
        figdir,
        f"df_state_sfr_surf_allsites.csv"
    )
    df.to_csv(TABLE_FILE)

    print(f"Table available at: {TABLE_FILE}")

create_table_sfr_all_sites(sites, sim_codes)