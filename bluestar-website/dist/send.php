<?php
// Minimaler Kontaktformular-Versand. Voraussetzung: PHP + mail() auf dem Hosting.
$to = 'hallo@bluestar.direct';
if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !empty($_POST['website'])) { http_response_code(400); exit; }
$name  = trim(preg_replace('/[\r\n]+/', ' ', $_POST['name'] ?? ''));
$email = filter_var(trim($_POST['email'] ?? ''), FILTER_VALIDATE_EMAIL);
$msg   = trim($_POST['message'] ?? '');
if (!$name || !$email || !$msg || empty($_POST['privacy'])) { http_response_code(400); exit('Bitte alle Felder ausfüllen.'); }
$ok = mail($to, '=?UTF-8?B?' . base64_encode("Kontaktanfrage von $name") . '?=', $msg,
  ["From: no-reply@bluestar.direct", "Reply-To: $email", "Content-Type: text/plain; charset=UTF-8"]);
header('Content-Type: text/html; charset=utf-8');
echo $ok ? '<p>Vielen Dank, wir melden uns zeitnah. <a href="kontakt.html">Zurück</a></p>' : '<p>Senden fehlgeschlagen. Bitte schreiben Sie an hallo@bluestar.direct.</p>';
