import pandas as pd
import matplotlib.pyplot as plt

''' Plots timeseries of T2 and RH2 for a grid cell of choice.
If netatmo stations are available for that grid cell, they are 
added as well. In addition, correlation and bias are provided.'''

plt.rcParams.update({'font.size': 14})
vars_to_plot = ['T2']

# Directories
fn_fig = "/home/demuzmp4/Nextcloud/scripts/supy-lcz-global/data/figs"

def _get_color_schemes(scheme):
    '''helper function to get color schemes'''

    cb = {
        'lcz': [
            '#8c0000', '#d10000', '#ff0000', '#bf4d00',
            '#ff6600', '#ff9955', '#faee05', '#bcbcbc',
            '#ffccaa', '#555555', '#006a00', '#00aa00',
            '#648525', '#b9db79', '#000000', '#fbf7ae', '#6a6aff'],

        # 'Paved (-)', 'Buildings (-)', 'Grass (-)',
        # 'Deciduous trees (-)', 'Evergreen trees (-)', 'Bare soil (-)', 'Water (-)'
        'suews': [
            '#4d4d4d', '#d05e5e', '#c5f776',
            '#5ac18e', '#156475', '#99774d', '#6a6aff']
    }

    return cb[scheme]
cb_lcz = _get_color_schemes('lcz')

fig, axes = plt.subplots(1, 1, figsize=(15 ,7))

# Find netatmo ID's within grid ID nr X
net_id_sel = list(net_stn[net_stn.index == grid_id_sel].netatmo_id)
len(net_id_sel)

for v_i, v in enumerate(vars_to_plot):

    # If netatmo stations available in grid cell, plot single stations.
    if len(net_id_sel) > 0:

        # Single station information
        for net_id_i in net_id_sel:
            net_obs_sel = net_obs[net_obs.id == net_id_i][v]
            net_obs_sel = net_obs_sel.resample('1H').last()
            net_obs_sel = net_obs_sel.loc[sub_start:sub_end]
            if not net_obs_sel.empty:
                net_obs_sel.plot(ax=axes, legend=False, lw=1,
                                 color=cb_lcz[int(net_stn[net_stn.netatmo_id == net_id_i]['LCZ'] ) -1])
                net_obs_avg = net_obs_sel

    # If # netatmo > 1, also plot average
    if len(net_id_sel) > 1:
        net_obs_avg = net_obs[net_obs.id.isin(net_id_sel)][v] \
                          .loc[sub_start:sub_end] \
            .groupby('date').mean()
        net_obs_avg.plot(ax=axes ,linestyle='--', color="#9932cc", lw=2)

    list_grid = pd.to_numeric(df_output.index.levels[0], downcast="integer")
    df_output.index = df_output.index.set_levels(list_grid, level=0)
    df_output = df_output.sort_index()

    suews_sel = df_output.loc[grid_id_sel, [v]] \
                    .loc[sub_start:sub_end]
    suews_sel.plot(ax=axes, color='black', legend=False ,lw=2)

    # Also add few statistics, if netatmo stations are available
    if len(net_id_sel) > 0:
        tmp = pd.merge(suews_sel ,pd.DataFrame(net_obs_avg), how='inner', left_index=True, right_index=True)
        corr = np.round(tmp[ v +'_x'].corr(tmp[ v +'_y']) ,2)
        bias = np.round((tmp[ v +'_x' ] -tmp[ v +'_y']).mean() ,2)
        print(corr, bias)

        axes.set_title(f'Correlation: {corr} | Bias: {bias} ' ,loc='right')

axes.set_ylabel('2m Temperature ($^\circ C$)')
# axes[1].set_ylabel('2m Relative Humidity (%)')

# Add custom legend in top panel
custom_lines = [Line2D([0], [0], color='black', lw=2),
                Line2D([0], [0], color='#ff0000', lw=1),
                Line2D([0], [0], color='#9932cc', lw=2, ls='--')]

axes.legend(custom_lines, ['SUEWS' ,'Netatmo station (LCZ color)', 'Netatmo average'])

axes.set_title(f'Grid ID: {grid_id_sel} | # Netatmo stations: {len(net_id_sel)} ' ,loc='left')

plt.tight_layout()

fig.savefig(os.path.join(
    fn_fig,
    f"plot_timeseries_grid_cell_{grid_id_sel}_{sub_start}_{sub_end}.jpg"),
    dpi = 300)
