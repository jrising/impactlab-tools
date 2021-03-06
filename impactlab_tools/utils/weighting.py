import numpy as np
import xarray as xr


# Computation helpers

def weighted_quantile_xr(
        data,
        quantiles,
        sample_weight,
        dim,
        values_sorted=False):
    """
    Compute quantiles of a weighted distribution

    similar to :py:func:`weighted_quantile` operates on a named dimension of an
    :py:class:`xarray.DataArray`.

    .. NOTE ::

        quantiles should be in [0, 1]!

    Parameters
    ----------

    data : DataArray

        xarray.DataArray with data

    quantiles : array-like

        quantiles of distribution to return

    sample_weight : numpy.array

        weights array-like of the same length as `array`

    values_sorted : bool

        if True, then will avoid sorting of initial array

    dim : str

        Dimension along which to weight the data

    Returns
    -------

    xarray.DataArray

        computed quantiles from weighted distribution

    """

    axis = data.get_axis_num(dim)
    dims = list(data.dims[:axis]) + ['quantile'] + list(data.dims[axis+1:])
    coords = {
        coord: data.coords[coord] for coord in data.dims if coord in dims}
    coords.update({'quantile': quantiles})

    data_dist = weighted_quantile(
        data.values,
        quantiles,
        sample_weight.loc[data.coords[dim].values].values,
        values_sorted=values_sorted,
        axis=axis)

    data_dist = xr.DataArray(data_dist, dims=dims, coords=coords)

    return data_dist


def weighted_quantile(
        values,
        quantiles,
        sample_weight=None,
        values_sorted=False,
        old_style=False,
        axis=None):
    """
    Compute quantiles of a weighted distribution

    similar to :py:func:`weighted_quantile_1d` but supports weighting along any
    (numbered) dimension

    .. NOTE ::

        quantiles should be in [0, 1]!

    Parameters
    ----------

    values : numpy.array

        numpy.array with data

    quantiles : array-like

        quantiles of distribution to return

    sample_weight : numpy.array

        weights array-like of the same length as `array`

    values_sorted : bool

        if True, then will avoid sorting of initial array

    old_style : bool

        if True, will correct output to be consistent with numpy.percentile.

    Returns
    -------

    numpy.array

        computed quantiles from weighted distribution

    """
    if len(values.shape) > 1 and axis is not None:

        return np.apply_along_axis(
            weighted_quantile_1d,
            axis,
            values,
            quantiles,
            sample_weight,
            values_sorted,
            old_style)

    else:

        return weighted_quantile_1d(
            values,
            quantiles,
            sample_weight,
            values_sorted,
            old_style)


def weighted_quantile_1d(
        values,
        quantiles,
        sample_weight=None,
        values_sorted=False,
        old_style=False):
    """
    Very close to numpy.percentile, but supports weights

    Thanks to Alleo!
    http://stackoverflow.com/questions/21844024/weighted-percentile-using-numpy/29677616#29677616

    .. NOTE ::

        quantiles should be in [0, 1]!

    Parameters
    ----------

    values : numpy.array

        numpy.array with data

    quantiles : array-like

        quantiles of distribution to return

    sample_weight : numpy.array

        weights array-like of the same length as `array`

    values_sorted : bool

        if True, then will avoid sorting of initial array

    old_style : bool

        if True, will correct output to be consistent with numpy.percentile.

    Returns
    -------

    numpy.array

        computed quantiles from weighted distribution

    """
    values = np.array(values)
    quantiles = np.array(quantiles)

    if sample_weight is None:
        sample_weight = np.ones(len(values))

    sample_weight = np.array(sample_weight)

    msg = 'quantiles should be in [0, 1]'
    assert np.all(quantiles >= 0) and np.all(quantiles <= 1), msg

    if not values_sorted:

        sorter = np.argsort(values)
        values = values[sorter]
        sample_weight = sample_weight[sorter]

    weighted_quantiles = np.cumsum(sample_weight) - 0.5 * sample_weight

    if old_style:

        # To be convenient with np.percentile
        weighted_quantiles -= weighted_quantiles[0]
        weighted_quantiles /= weighted_quantiles[-1]

    else:

        weighted_quantiles /= np.sum(sample_weight)

    result = np.interp(quantiles, weighted_quantiles, values)

    return result
