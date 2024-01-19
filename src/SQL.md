
### 2024-01-19
``` sql 
UPDATE volunteer.v_list
SET 
	squad = '阿公店溪、典寶溪分隊'
WHERE 
	squad IN ('阿公店溪分隊', '典寶溪分隊', '阿公店溪、典寶溪分隊')
;
```
