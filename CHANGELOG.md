# Changelog

<!--next-version-placeholder-->

## v4.0.0 (2021-09-09)
### Feature
* Add overwrite/automatic/manual cache policies ([`a013b69`](https://github.com/kalekundert/autoprop/commit/a013b69e1222918e776899d81eab29417eab0af0))

### Breaking
* remove property/object/class cache policies.  ([`a013b69`](https://github.com/kalekundert/autoprop/commit/a013b69e1222918e776899d81eab29417eab0af0))

### Documentation
* Describe how to manually clear the cache ([`7a526e7`](https://github.com/kalekundert/autoprop/commit/7a526e73b9c9ca39d9813cdeb10abba8d1f73059))

## v3.0.0 (2021-05-27)
### Feature
* Change default cache policy to 'property' ([`a3baec5`](https://github.com/kalekundert/autoprop/commit/a3baec55ceee721c9090dc2a5639ac686eb6170e))

### Breaking
* the new default caches more aggressively, so code written with the old default may end up with stale values.  Update old code by replacing `@autoprop.cache` with `@autoprop.cache(policy='object')`.  ([`a3baec5`](https://github.com/kalekundert/autoprop/commit/a3baec55ceee721c9090dc2a5639ac686eb6170e))

## v2.2.0 (2021-04-05)
### Feature
* Add the `immutable` decorator ([`e8f023a`](https://github.com/kalekundert/autoprop/commit/e8f023ab099b3d1477bb285267e11528c43c4f5c))

## v2.1.1 (2021-04-01)
### Fix
* Cache getters (not just properties) ([`ab454eb`](https://github.com/kalekundert/autoprop/commit/ab454eb1d247b147675fc6c377747892588762c1))

### Documentation
* Reorganize the caching section ([`f7ac9bb`](https://github.com/kalekundert/autoprop/commit/f7ac9bb79ac7764f9227601dd6108c756e934704))
* Fix typo ([`613e180`](https://github.com/kalekundert/autoprop/commit/613e180067aa646e9696e70b88435f3962b37c5c))
* Tweak wording ([`b009007`](https://github.com/kalekundert/autoprop/commit/b009007a819d5bdb71c82dae7d539dca2804edf9))
* Fix formatting ([`11b027f`](https://github.com/kalekundert/autoprop/commit/11b027f36a71f0d94352d3f6911844d0308f222b))
* Improve the first example ([`8e365a1`](https://github.com/kalekundert/autoprop/commit/8e365a1b19f1ab3553ec9346e6e2ed59f132b029))

## v2.1.0 (2021-03-31)
### Feature
* Only configure caching if requested ([`109f430`](https://github.com/kalekundert/autoprop/commit/109f430fd286e139ed2fef02777d106be2334df2))

### Fix
* Don't have *every* static/class method invalidate the cache ([`a231052`](https://github.com/kalekundert/autoprop/commit/a231052fb038260055ad5bdaa860e2e25eb4f5a3))

### Documentation
* Document the caching system ([`1974c42`](https://github.com/kalekundert/autoprop/commit/1974c42e0f33859c6c282869cbb861b2c9a8a3de))

## v2.0.0 (2021-03-30)
### Feature
* Drop support for python 3.5 ([`d4781cb`](https://github.com/kalekundert/autoprop/commit/d4781cb489a0a74987ca96eb390d4e1dd507ff47))
* Implement caching policies ([`a05726a`](https://github.com/kalekundert/autoprop/commit/a05726aa96ccce670274430180272dd2c72c3df5))

### Breaking
* Drop support for python2.  ([`a05726a`](https://github.com/kalekundert/autoprop/commit/a05726aa96ccce670274430180272dd2c72c3df5))

### Documentation
* Remove python2 badge ([`815c60d`](https://github.com/kalekundert/autoprop/commit/815c60d5d81d82f567baba2df4b927bc4cbbc224))
