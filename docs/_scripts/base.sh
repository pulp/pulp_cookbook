: "${BASE_ADDR:=http://localhost}"
: "${CONTENT_ADDR:=http://localhost}"

# Poll a Pulp task until it is finished.
wait_until_task_finished() {
    local task_url=$1
    while true
    do
        local response=$(http --pretty format "$task_url")
        local state=$(jq -r .state <<< "${response}")
        case ${state} in
            failed|canceled)
                cat <<< "${response}" >&2
                echo "Task in final state: ${state}" >&2
                break
                ;;
            completed)
                cat <<< "${response}"
                break
                ;;
            *)
                echo "Waiting for task completion. Task:" >&2
                cat <<< "${response}" >&2
                sleep 1
                ;;
        esac
    done
}

pulp_http() {
    local response=$(http --pretty format "$@")
    local task_url=$(jq -r '.task' <<< "$response")
    if [[ "$task_url" == "null" ]]; then
        cat <<< "$response"
    else
        wait_until_task_finished "$BASE_ADDR$task_url"
    fi
}
