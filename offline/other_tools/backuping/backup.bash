#!/usr/bin/env bash

# Deliberate choice is made to lower load on server (therefore no compression)

# Script will stop if a command returns an error code
set -e 

# Disable screen saver etc for one hour (script should take less than that)
systemd-inhibit --why="Backup in progress" --mode=block bash -c "
  echo 'Start of screen saver inihibit'
  sleep 3600
  echo 'End of screen saver inihibit'
" &


# sshpass needs to be installed on backup machine
# sqlite3 needs to be installed on server
# mongodb needs to be installed on backup machine
# rclone needs to be installed on backup machine (and credentials in ~/.config/rclone/rclone.conf)

SERVER_USERNAME="ubuntu"
SERVER_ADDRESS="37.59.100.228"
MONGODB_PORT=27017
MONGODB_DATABASE_NAME=nodebb
MONGODB_DATABASE_USER=nodebb
GOOGLE_DRIVE=backup_diplomania

# If script recives interruption signal, it stops completely
trap "exit" INT

# Time of script execution
start_time=$(date +%s)

# Backup  time stamp
now=$(date +%Y%m%d)

# Only one possible parameter
if [ ! "$1" == "-f" ]; then
    echo "Use -f parameter for fast mode (only Flasks APIs)"
    echo
fi

# Need server machine password
if [ -z "${SERVER_PASSWORD}" ]; then
    echo "Please define SERVER_PASSWORD !"
    exit 1
fi

if [ ! -d ./backups ]; then
    mkdir ./backups
fi

# Create a fresh backup dir
backup_dir=./backups/${now}
if [ -d ${backup_dir} ]; then
     rm -fr ${backup_dir}
fi
mkdir ${backup_dir}

echo "================"
echo "Backuping Flask APIs ..."
echo "================"
echo

for service in users players games ; do

    # do backup 
    echo "Backuping db ${service}..."
    backup_distant_db_file=/tmp/backup_db_${service}_${now}.db
    cmd="sqlite3 ./api_flask/${service}_service/db/${service}.db '.backup ${backup_distant_db_file}'"
    sshpass -p "${SERVER_PASSWORD}" ssh ${SERVER_USERNAME}@${SERVER_ADDRESS} ${cmd}

    # do dump
    echo "Dumping sql ${service}..."
    dump_sql_distant_file=/tmp/dump_db_${service}_${now}.sql.gz
    cmd="sqlite3 ./api_flask/${service}_service/db/${service}.db .dump > ${dump_sql_distant_file}"
    sshpass -p "${SERVER_PASSWORD}" ssh ${SERVER_USERNAME}@${SERVER_ADDRESS} ${cmd}

    # bring backup db here on backup machine
    echo "Bringing locally ${service} backup db file"
    backup_local_db_file=backup_db_${service}_${now}.db
    SECONDS=0
    sshpass -p "${SERVER_PASSWORD}" rsync -aqz ${SERVER_USERNAME}@${SERVER_ADDRESS}:${backup_distant_db_file} ${backup_local_db_file}
    echo "Took $SECONDS seconds"

    # bring sql dump here on backup machine
    echo "Bringing locally ${service} sql dump file"
    dump_local_sql_file=dump_db_${service}_${now}.sql.gz
    SECONDS=0
    sshpass -p "${SERVER_PASSWORD}" rsync -aqz ${SERVER_USERNAME}@${SERVER_ADDRESS}:${dump_sql_distant_file} ${dump_local_sql_file}
    echo "Took $SECONDS seconds"

    # compress backup
    echo "Compress ${service} backup db file"
    backup_local_file=${backup_local_db_file}.tar.gz
    SECONDS=0
    tar czf ${backup_local_file} ${backup_local_db_file}
    echo "Took $SECONDS seconds"
    echo "Delete ${service} dump file"
    rm ${backup_local_db_file}

    # compress sql dump
    echo "Compress ${service} dump sql file"
    dump_local_file=${dump_local_sql_file}.tar.gz
    SECONDS=0
    tar czf ${dump_local_file} ${dump_local_sql_file}
    echo "Took $SECONDS seconds"
    echo "Delete ${service} dump file"
    rm ${dump_local_sql_file}

    # delete backup sql and dump db from server
    echo "Deleting from server ${service} files"
    cmd="rm ${backup_distant_db_file} && rm ${dump_sql_distant_file}"
    sshpass -p "${SERVER_PASSWORD}" ssh ${SERVER_USERNAME}@${SERVER_ADDRESS} ${cmd}

    # move to backup dir
    echo "Moving to backup dir ${service} files"
    mv ${backup_local_file} ${backup_dir}/
    mv ${dump_local_file} ${backup_dir}/

    echo
    sleep 2

done

if [ "$1" == "-f" ]; then
    echo "Fast mode selected. Exiting"
    exit 0
fi

echo "================"
echo "Backuping Forum ..."
echo "================"
echo

if [ -z "${MONGODB_DATABASE_PASSWORD}" ]; then
    echo "Please define MONGODB_PASSWORD !"
    exit 1
fi

backup_local_dir=nodebb-${now}
backup_local_file=nodebb-${now}.tar

echo "Backuping forum database"
if [ -d ${backup_local_dir} ]; then
    rm -fr ${backup_local_dir}
fi
mkdir ${backup_local_dir}
SECONDS=0
echo "Mongodump command"
mongodump --host ${SERVER_ADDRESS} --port ${MONGODB_PORT} --db ${MONGODB_DATABASE_NAME} --out ${backup_local_dir} --gzip --authenticationMechanism SCRAM-SHA-256 --username ${MONGODB_DATABASE_USER} --password ${MONGODB_DATABASE_PASSWORD} --quiet
echo "Took $SECONDS seconds"

# tar dir to single file
SECONDS=0
echo "tar to single file"
tar cf ${backup_local_file} ${backup_local_dir}
echo "Took $SECONDS seconds"
rm -fr ${backup_local_dir}

# move to backup dir
echo "Moving to backup mongodb file"
mv ${backup_local_file} ${backup_dir}/

echo

echo "Bringing locally uploads files"
backup_local_directory=./uploads-${now}
if [ -d ${backup_local_directory} ]; then
    rm -fr ${backup_local_directory}
fi
backup_distant_directory=/home/ubuntu/forum_nodebb/data/nodebb/uploads
SECONDS=0
sshpass -p "${SERVER_PASSWORD}" rsync -aqz ${SERVER_USERNAME}@${SERVER_ADDRESS}:${backup_distant_directory} ${backup_local_directory}
echo "Took $SECONDS seconds"

echo "Compressing uploads dir"
backup_local_file=uploads-${now}.tar.gz
SECONDS=0
tar -czf ${backup_local_file} ${backup_local_directory}
echo "Took $SECONDS seconds"
rm -fr ${backup_local_directory}

echo "Moving to backup dir uploads file"
mv ${backup_local_file} ${backup_dir}/

echo

echo "================"
echo "Backuping Wikis ..."
echo "================"
echo

for wiki in dokuwiki-data dokuwiki-data2 ; do

    echo "Backuping ${wiki}..."
    echo

    backup_local_directory=./${wiki}-${now}
    if [ -d ${backup_local_directory} ]; then
        rm -fr ${backup_local_directory}
    fi

    # data/attic is too big and causes "broken pipe"
    for item in data/pages data/media data/meta lib/plugins lib/tpl conf ; do

        echo "Bringing locally ${wiki} ${item} files"
        backup_local_item_directory=./${backup_local_directory}/${item//\//_}
        mkdir -p ${backup_local_item_directory}
        backup_distant_item_directory=/home/ubuntu/wiki_doku/${wiki}/${item}
        SECONDS=0
        sshpass -p "${SERVER_PASSWORD}" rsync -aqz ${SERVER_USERNAME}@${SERVER_ADDRESS}:${backup_distant_item_directory} ${backup_local_item_directory}
        echo "Took $SECONDS seconds"

        echo
        sleep 2

    done

    echo "Compressing ${wiki}  dir"
    backup_local_file=${wiki}-${now}.tar.gz
    SECONDS=0
    tar -czf ${backup_local_file} ${backup_local_directory}
    echo "Took $SECONDS seconds"
    rm -fr ${backup_local_directory}

    echo "Moving to backup dir ${wiki} file"
    mv ${backup_local_file} ${backup_dir}/

    echo

done

echo

echo "================"
echo "Exporting to drive ..."
echo "================"
echo

echo "Moving artefacts to google drive..."
archive_dir=${now}
rclone mkdir ${GOOGLE_DRIVE}:${archive_dir}
for file in $(ls ${backup_dir}) ; do 
    echo
    echo "Moving ${file} to google drive..."
    rclone copy ${backup_dir}/${file} ${GOOGLE_DRIVE}:${archive_dir}/ --bwlimit 2M --transfers 1 --checkers 1 --progress
    sleep 2
done

# Removing artefacts from here
rm -fr ${backup_dir}

end_time=$(date +%s)
duration=$((end_time - start_time))

echo
echo "Script took $((duration / 60)) minutes $((duration % 60)) seconds."

# TODO run endlessly
### now=$(date +%s)
### target=$(date -d "tomorrow 04:00" +%s)
### sleep $(( target - now ))

# TODO : send email
# mailutils msmtp msmtp-mta etc
# echo "content" | mail -s "subject" <dest>

# Re-enable screen saver

