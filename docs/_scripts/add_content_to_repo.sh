pulp_http POST $BASE_ADDR$REPO_HREF'modify/' add_content_units:="[\"$UBUNTU_CONTENT_HREF\",\"$APT_CONTENT_HREF\"]"
export LATEST_VERSION_HREF=$(http $BASE_ADDR$REPO_HREF | jq -r '.latest_version_href')
