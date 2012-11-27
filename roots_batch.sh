#!/bin/bash -x
PY_DIR=$PWD
#ITER=10000
if [ -z $ITER ]; then
	ITER=5000
fi
if [ -z $PRECISION ]; then
	PRECISION=13
fi
if [ -z $SYMMETRY ]; then
	SYMMETRY=A4
fi
if [ -z $GIT_DIR ]; then
	GIT_DIR=$PWD/batch_search/frh-$SYMMETRY
fi
if [ -z $TMP_DIR ]; then
	TMP_DIR=$GIT_DIR/tmp
fi
if [ -z $BAC_DIR ]; then
	BAC_DIR=$TMP_DIR/.bac
fi
if [ -z $SEARCH_SCRIPT ]; then
	SEARCH_SCRIPT=roots_batch.py
fi
if [ -z $FILTER_SCRIPT ]; then
	FILTER_SCRIPT=filter.py
fi
if [ -z $SOLS_COUNT_FILE ]; then
	SOLS_COUNT_FILE=sols_count.csv
fi
if [ -z $EXIT_CODE_FILE ]; then
	EXIT_CODE_FILE=exit_codes
fi

check_and_create_dirs() {
	for DIR in $GIT_DIR $TMP_DIR ; do {
		if [ ! -d "$DIR" ] ; then {
			mkdir -p "$DIR"
		} fi
		if [ ! -d $DIR ] ; then {
			echo "Oops: $DIR failed to create directory"
			exit -1
		} fi
	} done
}

setup_py_script_links() {
	for SCRIPT in $SEARCH_SCRIPT $FILTER_SCRIPT ; do {
		if [ ! -h $SCRIPT ] ; then {
			ln -s $PY_DIR/$SCRIPT || exit -1
		} fi
	} done
}

# This can be usefull if you want to change the script:
# - interrupt the script by Ctrl-C,
# - copy back the files from the back-up dir,
# - change the script.
# - restart the script.
# If you don't do this, the problem is that the variable "iterations" becomes
# incorrect, since not all files are copied to the git.
backup_current_solutions() {
	rm -fr $BAC_DIR
	mkdir $BAC_DIR
	cp $TMP_DIR/frh*.py $BAC_DIR
}

set_doms_for_3_threads() {
	if [ "$SYMMETRY" == "A4" ] ; then
		DOMS="[0:9] [9:18] [18:]"
	elif [ "$SYMMETRY" == "S4" ] ; then
		DOMS="[0:10] [10:20] [20:]"
	fi
}

run_and_check_result() {
	# ignores race condition
	$CMD || echo $((`cat $EXIT_CODE_FILE`+1)) > $EXIT_CODE_FILE
}

search_for_solutions() {
	echo 0 > $EXIT_CODE_FILE
	for DOM in $DOMS ; do {
		CMD="python $SEARCH_SCRIPT -i $ITER -o $TMP_DIR -p $PRECISION -s -l $DOM $SYMMETRY"
		run_and_check_result &
	} done
	wait
	RETURN=`cat $EXIT_CODE_FILE`
	if [ $RETURN != "0" ] ; then {
		echo "An error occurred in $RETURN of the search processes"
		exit $((-RETURN))
	} fi
	rm $EXIT_CODE_FILE
}

copy_to_git_dir_if_sols_found() {
	python $FILTER_SCRIPT $GIT_DIR $TMP_DIR
}

git_init_if_none() {
	if [ ! -d .git ]; then {
		GIT_INIT="YES"
		git init
	} fi
}

git_add_modified_with_new_sols() {
	MOD_FILES=$(git status | grep modified | awk '{print $3}')
	for FILE in $MOD_FILES; do
		# grep addition of solutions
		GREP_RES=$(git diff "$FILE" | grep -e '^\+    \[')
		# grep deletion of solutions
		GREP_RES="$GREP_RES$(git diff "$FILE" | grep -e '^\-    \[')"
		if [ -n "$GREP_RES" ] ; then
			IS_DYN=$(echo "$DYN_FILES" | grep "$FILE")
			if [ -z $IS_DYN ] ; then
				git add "$FILE"
			fi
		fi
	done
}

git_add_new_files() {
	NEW_FILES=$(git status | grep -e '#	frh-roots.*.py' | awk '{print $2}')
	for FILE in $NEW_FILES; do
		GREP_RES=$(grep -e '^    \[' "$FILE" )
		if [ -n "$GREP_RES" ] ; then
			IS_DYN=$(echo "$DYN_FILES" | grep "$FILE")
			if [ -z $IS_DYN ] ; then
				git add "$FILE"
			fi
		fi
	done
}

git_count_added_removed_sols() {
	if [ -z $GIT_INIT ] ; then {
		NR_OF_NEW_SOLS=$(git diff --cached | grep -c '^\+    \[')
		NR_OF_RMED_SOLS=$(git diff --cached | grep -c '^\-    \[')
	} else {
		NR_OF_NEW_SOLS=$(cat frh-roots*.py | grep -c '^    \[')
		NR_OF_RMED_SOLS='0'
	} fi
}

git_create_commit_message() {
	MSG=$(date +%Y-%m-%d)
	MSG="$MSG: Add $NR_OF_NEW_SOLS solution"
	# MSG grammar: use plural if more than 1 solution
	if (($NR_OF_NEW_SOLS > 1)) ; then
		MSG="$MSG"s
	fi
	# Add removals to MSG
	if (($NR_OF_RMED_SOLS > 0)) ; then
		MSG="$MSG (delete $NR_OF_RMED_SOLS)"
	fi
}

git_commit_if_needed() {
	NETTO_NR_OF_SOLS=$(($NR_OF_NEW_SOLS - $NR_OF_RMED_SOLS))
	if [ -z $GIT_INIT ] ; then {
		echo "$ITER:$NETTO_NR_OF_SOLS" >> $SOLS_COUNT_FILE
	} else {
		echo "$ITER:$NETTO_NR_OF_SOLS" > $SOLS_COUNT_FILE
	} fi
	git add $SOLS_COUNT_FILE
	if [[ (($NR_OF_NEW_SOLS > 0)) || (($NR_OF_RMED_SOLS > 0)) ]] ; then
		git commit -m "$MSG"
		echo "commited \"$MSG\""
		if (($NR_OF_RMED_SOLS > 0)) ; then
			echo "**** Warning: the commit removes $NR_OF_RMED_SOLS existing solution(s)"
		fi
		unset GIT_INIT
	else
		git commit --amend -C HEAD -n
		echo "Nothing to commit"
	fi
}

check_and_create_dirs
cd $TMP_DIR
setup_py_script_links

while true; do {
	backup_current_solutions
	set_doms_for_3_threads
	search_for_solutions

	# copy only the ones containing a solution
	copy_to_git_dir_if_sols_found

	# do the git stuff
	cd $GIT_DIR
	git_init_if_none
	git_add_modified_with_new_sols
	git_add_new_files
	git_count_added_removed_sols
	git_create_commit_message
	git_commit_if_needed
	# ignore all files that are just an increase of the nr of iterations:
	# or dynamic files
	git reset --hard
	cd $TMP_DIR
} done
