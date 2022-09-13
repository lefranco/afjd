<?php
/*
* Description: example file for displaying latest posts and topics
* by battye (for phpBB.com MOD Team)
* September 29, 2009
* Modified for StackOverflow Question: http://stackoverflow.com/questions/14723578/phpbb3-forum-feed-on-external-page-for-non-authenticated-users
*/

define('IN_PHPBB', true);

define('PHPBB_ROOT_PATH', './forum/phpBB3/');

$phpbb_root_path = (defined('PHPBB_ROOT_PATH')) ? PHPBB_ROOT_PATH : './';
$phpEx = substr(strrchr(__FILE__, '.'), 1);
include($phpbb_root_path . 'common.' . $phpEx);
include($phpbb_root_path . 'includes/bbcode.' . $phpEx);
include($phpbb_root_path . 'includes/functions_display.' . $phpEx);

// Start session management
$user->session_begin();
$auth->acl($user->data);
$user->setup('viewforum');

$search_limit = 10;

$posts_ary = array(
        'SELECT'    => 'p.*, t.*, u.username, u.user_colour',

        'FROM'      => array(
            POSTS_TABLE     => 'p',
        ),

        'LEFT_JOIN' => array(
            array(
                'FROM'  => array(USERS_TABLE => 'u'),
                'ON'    => 'u.user_id = p.poster_id'
            ),
            array(
                'FROM'  => array(TOPICS_TABLE => 't'),
                'ON'    => 'p.topic_id = t.topic_id'
            ),
        ),

        'WHERE'     => $db->sql_in_set('t.forum_id', array_keys($auth->acl_getf('f_read', true))) . '
                        AND t.topic_status <> ' . ITEM_MOVED ,

        'ORDER_BY'  => 'p.post_id DESC',
    );

    $posts = $db->sql_build_query('SELECT', $posts_ary);

    $posts_result = $db->sql_query_limit($posts, $search_limit);

      while( $posts_row = $db->sql_fetchrow($posts_result) )
      {
         $topic_title       =  $posts_row['topic_title'];
         $post_author       =  $posts_row['username']; // get_username_string('full', $posts_row['poster_id'], $posts_row['username'], $posts_row['user_colour']);
         $post_date          = $user->format_date($posts_row['post_time']);
         $post_link       = append_sid("{$phpbb_root_path}viewtopic.$phpEx", "p=" . $posts_row['post_id'] . "#p" . $posts_row['post_id']);

         $post_text = nl2br($posts_row['post_text']);

         $bbcode = new bbcode(base64_encode($bbcode_bitfield));         
         $bbcode->bbcode_second_pass($post_text, $posts_row['bbcode_uid'], $posts_row['bbcode_bitfield']);

         $post_text = smiley_text($post_text);

         $template->assign_block_vars('announcements', array(
         'TOPIC_TITLE'       => censor_text($topic_title),
         'POST_AUTHOR'       => $post_author,
         'POST_DATE'       => $post_date,
         'POST_LINK'       => $post_link,
         'POST_TEXT'         => censor_text($post_text),
         ));
      }

	page_header('External page');

    $template->set_filenames(array(
        'body' => 'external_body.html'
    ));

    page_footer();


?>