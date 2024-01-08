### 更新年度資料

``` sql
    WITH 
        pre AS (
            SELECT 
                sn_excel, org, v_id, v_name, v_character
                , basin_id, basin_name, region, squad
                , patrol_area_id, patrol_area_name
                , note, member, couple_group, 2024
            FROM
                volunteer.v_list
            WHERE 
                year = 2023 AND sn_excel > 0
        )
    INSERT INTO volunteer.v_list(
        sn_excel, org, v_id, v_name, v_character, basin_id, basin_name, region, squad, patrol_area_id, patrol_area_name, note, member, couple_group, year)
    SELECT * FROM pre
    ;
```


### 更新
``` sql
    SELECT 
        sn_excel, org, v_id, v_name, v_character, basin_id, basin_name, region, squad, patrol_area_id, patrol_area_name, note, member, couple_group, year
    FROM 
        volunteer.v_list
    WHERE 
        year = 2024 AND sn_excel > 0
        AND v_name IN (
            '林文鍠'
            , '王清崎', '梁永賢'
            , '吳月桃', '李依宸'
            , '李清泰', '吳沂謙'
            , '黃連富', '余奕靖'
            , '江春龍', '劉新業'
            , '周明良', '梁永賢'
        )
    ORDER BY
        v_character ASC
    ;
```