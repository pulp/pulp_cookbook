task_result=$(pulp_http POST $BASE_ADDR/pulp/api/v3/publications/cookbook/cookbook/ repository_version=$LATEST_VERSION_HREF)
echo "$task_result"
export PUBLICATION_HREF=$(echo "$task_result" | jq -r '.created_resources[0]')
