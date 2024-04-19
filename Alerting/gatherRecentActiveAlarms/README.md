# Gather Recent Active Alarms

## Description
Program that gathers recent active alarms exactly as can be seen in the alerting tab of the product. Results are json format. 

## TO USE
Start by creating the necessary auth file under the modules folder. Follow the sample auth file. 

Next, install the requirements file. 

Next, set the necessary parameters in the inputs module file. 

Then, determine if the outputs module gives you what you need. 

Finally, run the program. 

## Available paramaters for the /alarms api endpoint

Name: limit
string($uint64)
(query)
Description
- limit is how many alarms to return at most. Defaults to 100.
Default value : 100

---

Name: offset
string($uint64)
(query)
Description
- offset is the offset into the list of alarms. Use this for paging.
Default value : 0

---

Name: pageToken
string
(query)
Description
- for alternative pagination schema instead of offset.

pageToken
sortBy
string
(query)
Description
- sorting configuration in format field:order e.g. start_time:asc, by default no sorting.

sortBy
start
string($date-time)
(query)
Description
- start is a lower bound of timespan. Alarm duration has to overlap this timespan to get included in results (inclusive).

start
end
string($date-time)
(query)
Description
- end is a upper bound of timespan. Alarm duration has to overlap this timespan to get included in results (inclusive).

end
creationTimeStart
string($date-time)
(query)
Description
- creationTimeStart and creationTimeEnd bracket an alarm's creationTime.

creationTimeStart
creationTimeEnd
string($date-time)
(query)
creationTimeEnd
creationTimeDuration
string
(query)
creationTimeDuration
startTimeStart
string($date-time)
(query)
Description
- startTimeStart and startTimeEnd bracket an alarm's startTime.

startTimeStart
startTimeEnd
string($date-time)
(query)
startTimeEnd
startTimeDuration
string
(query)
startTimeDuration
endTimeStart
string($date-time)
(query)
Description
- endTimeStart and endTimeEnd bracket an alarm's endTime.

endTimeStart
endTimeEnd
string($date-time)
(query)
endTimeEnd
endTimeDuration
string
(query)
endTimeDuration
states
array[string]
(query)
Description
- states filters alarms to only those in these states. If not present, any state is allowed.
Available values : noneState, clear, alarm, ackReq
Default value : ["clear", "alarm", "ackReq"]

--noneStateclearalarmackReq
severities
array[string]
(query)
severities filters alarms to only those at these severities. If not present, any severity is allowed.

Available values : noneSeverity, minor, minor2, major, major2, critical

Default value : ["minor", "minor2", "major", "major2", "critical"]

--noneSeverityminorminor2majormajor2critical
mitigations
array[string]
(query)
Description
- mitigations narrows results to alarms with given mitigations associated.
Default value : []

policies
array[string]
(query)
Description
- policies narrows results to alarms with given policy associated.
Default value : []

alarms
array[string]
(query)
Description
- alarms filters results to alarms with these ids.

Default value : []

Name: policyNamePrefixes
array[string]
(query)
Description
- policyNamePrefixes filters results to alarms for policies whose names prefix-match.

Name: policyNames
array[string]
(query)
Description
- policyNames filters results to alarms for policies whose names match.

Name: ignorePolicies
array[string]
(query)
Name: ignorePolicyNamePrefixes
array[string]
(query)
Name: ignorePolicyNames
array[string]
(query)
Name: dimensionsConjunction
array[string]
(query)
Description
- dimensionsConjunction filters results to alarms for policies with all of these dimensions.

Name: dimensionsDisjunction
array[string]
(query)
Description
- dimensionsDisjunction filters results to alarms for policies with any of these dimensions.

--

Name: dimensions
array[string]
(query)
Description
- dimensions narrows results to alarms with all specified dimensions included.
Default value : []

--

Name: includeInsightAlarms
boolean
(query)
Description
- includeInsightAlarms includes Kentik-defined (insight) alarms. Default false = no insight alarms.

--

Name: excludeUserDefined
boolean
(query)
Description
- excludeUserDefined excludes user-defined alarms. Default false = alarms are included.

--

Name: pastOrPresent_unspecified
keyPartsExact
array[string]
(query)
Description
- keyPartsExact narrows results to alarms where all the specified key parts are present.

--

Name: keyPartsPartial
array[string]
(query)
Description
- keyPartsPartial narrows results to alarms where all the specified key parts are present via a partial match. Equivalent sql query keyPart ilike '%keyPartPartial%'.

--

Name: excludeSubpolicies
boolean
(query)
Description
- excludeSubpolices excludes Subpolicies alarms. Default false = alarms are included.

--
Name: applications
array[string]
(query)
