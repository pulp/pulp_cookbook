pulp_http POST $BASE_ADDR$REPO_HREF'sync/' mirror:=true
export LATEST_VERSION_HREF=$(http $BASE_ADDR$REPO_HREF | jq -r '.latest_version_href')