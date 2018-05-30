## All good example

Show all data.
```
jMeterLogSummary.py --test=ALLGOOD --log=https://raw.githubusercontent.com/rstyczynski/umc/master/varia/jmeter/jmeter_allgood.log --allResults
```

Limit only to max threads, ignoring ramp-iup and down.
```
jMeterLogSummary.py --test=ALLGOOD --log=https://raw.githubusercontent.com/rstyczynski/umc/master/varia/jmeter/jmeter_allgood.log
```

Limit time range.
```
jMeterLogSummary.py --test=ALLGOOD --log=https://raw.githubusercontent.com/rstyczynski/umc/master/varia/jmeter/jmeter_allgood.log --allResults --from="2018-05-29 23:55:00" --to="2018-05-30 00:05:00"
```

## Messy run example

Show all messy data.
```
jMeterLogSummary.py --test=ALLBAD --log=https://raw.githubusercontent.com/rstyczynski/umc/master/varia/jmeter/jmeter_allmessy.log --allResults
```

Limit only to max threads, ignoring ramp-iup and down.
```
jMeterLogSummary.py --test=ALLBAD --log=https://raw.githubusercontent.com/rstyczynski/umc/master/varia/jmeter/jmeter_allmessy.log
```

Limit time range.
```
jMeterLogSummary.py --test=ALLBAD --log=https://raw.githubusercontent.com/rstyczynski/umc/master/varia/jmeter/jmeter_allmessy.log  --allResults --from="2018-05-29 15:30:00" --to="2018-05-29 15:40:00" 
```

