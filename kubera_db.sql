CREATE TABLE `Healthcare_Providers` (
    `provider_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL
);

CREATE TABLE `Payors` (
    `payor_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL
);

CREATE TABLE `Documents` (
    `document_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `filename` VARCHAR(255) NOT NULL,
    `file_path` TEXT NOT NULL
);

CREATE TABLE `Contracts` (
    `contract_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `document_id` BIGINT UNSIGNED NOT NULL,
    `provider_id` BIGINT UNSIGNED NOT NULL,
    `payor_id` BIGINT UNSIGNED NOT NULL,
    `effective_date` DATE NOT NULL,
    `termination_date` DATE NOT NULL,
    `stop_loss_threshold` DECIMAL(8, 2) NOT NULL,
    `created_at` TIMESTAMP NOT NULL
);

CREATE TABLE `Amendments` (
    `amendment_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `contract_id` BIGINT UNSIGNED NOT NULL,
    `amendment_date` DATE NOT NULL,
    `document_id` BIGINT UNSIGNED NOT NULL,
    `created_at` TIMESTAMP NOT NULL
);

CREATE TABLE `Contract_Terms` (
    `term_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `contract_id` BIGINT UNSIGNED NOT NULL,
    `term_name` VARCHAR(255) NOT NULL,
    `term_value` TEXT NOT NULL,
    `created_at` TIMESTAMP NOT NULL
);

CREATE TABLE `Contract_Term_Revisions` (
    `revision_id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `contract_term_id` BIGINT UNSIGNED NOT NULL,
    `amendment_id` BIGINT UNSIGNED NOT NULL,
    `prev_value` TEXT NOT NULL,
    `new_value` TEXT NOT NULL,
    `changed_at` TIMESTAMP NOT NULL,
    `created_at` TIMESTAMP NOT NULL
);

ALTER TABLE `Contracts`
    ADD CONSTRAINT `contracts_payor_id_foreign` 
        FOREIGN KEY(`payor_id`) REFERENCES `Payors`(`payor_id`),
    ADD CONSTRAINT `contracts_document_id_foreign` 
        FOREIGN KEY(`document_id`) REFERENCES `Documents`(`document_id`),
    ADD CONSTRAINT `contracts_provider_id_foreign` 
        FOREIGN KEY(`provider_id`) REFERENCES `Healthcare_Providers`(`provider_id`);

ALTER TABLE `Amendments`
    ADD CONSTRAINT `amendments_contract_id_foreign` 
        FOREIGN KEY(`contract_id`) REFERENCES `Contracts`(`contract_id`),
    ADD CONSTRAINT `amendments_document_id_foreign` 
        FOREIGN KEY(`document_id`) REFERENCES `Documents`(`document_id`);

ALTER TABLE `Contract_Term_Revisions`
    ADD CONSTRAINT `contract_term_revisions_amendment_id_foreign` 
        FOREIGN KEY(`amendment_id`) REFERENCES `Amendments`(`amendment_id`),
    ADD CONSTRAINT `contract_term_revisions_contract_term_id_foreign` 
        FOREIGN KEY(`contract_term_id`) REFERENCES `Contract_Terms`(`term_id`);

ALTER TABLE `Contract_Terms`
    ADD CONSTRAINT `contract_terms_contract_id_foreign` 
        FOREIGN KEY(`contract_id`) REFERENCES `Contracts`(`contract_id`);