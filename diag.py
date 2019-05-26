from func import user_res
import matplotlib as mpl
import matplotlib.pyplot as plt

def make_diag(login, title, data_names, data_values):
    dpi = 80
    fig = plt.figure(dpi = dpi, figsize = (512 / dpi, 512 / dpi) )
    mpl.rcParams.update({'font.size': 9})

    plt.title(title)

    #xs = range(len(data_names))

    plt.pie( 
        data_values, autopct='%.1f', radius = 1.1,
        explode = [0.15] + [0 for _ in range(len(data_names) - 1)] )
    plt.legend(
        bbox_to_anchor = (-0.16, 0.45, 0.25, 0.25),
        loc = 'lower left', labels = data_names )
    fig.savefig(user_res(login) + 'diag.png')
