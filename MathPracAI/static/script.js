const dropdowns = document.querySelectorAll("[data-dropdown]");

function applyAuthAnimationPhase() {
  const panel = document.querySelector(".auth-visual-panel");
  if (!panel) {
    return;
  }

  const now = Date.now() / 1000;
  const phase = (duration, offset = 0) => `-${((now + offset) % duration).toFixed(3)}s`;
  const delays = {
    "--auth-shape-a-delay": phase(14, 0),
    "--auth-shape-b-delay": phase(16, 3),
    "--auth-geometry-delay": phase(26, 7),
    "--auth-symbol-a-delay": phase(15, 1),
    "--auth-symbol-b-delay": phase(17, 5),
    "--auth-symbol-c-delay": phase(19, 9),
    "--auth-symbol-d-delay": phase(16, 12),
    "--auth-symbol-e-delay": phase(18, 4),
    "--auth-symbol-f-delay": phase(14, 8),
    "--auth-symbol-g-delay": phase(20, 11),
    "--auth-symbol-h-delay": phase(22, 15),
    "--auth-text-delay": phase(14, 2),
  };

  Object.entries(delays).forEach(([name, value]) => {
    panel.style.setProperty(name, value);
  });
}

applyAuthAnimationPhase();

let firebaseAuthModulesPromise = null;
let firebaseAuthInstance = null;
let pendingGoogleNameRequest = null;

async function firebaseAuthModules() {
  if (!firebaseAuthModulesPromise) {
    firebaseAuthModulesPromise = Promise.all([
      import("https://www.gstatic.com/firebasejs/10.12.5/firebase-app.js"),
      import("https://www.gstatic.com/firebasejs/10.12.5/firebase-auth.js"),
    ]);
  }
  return firebaseAuthModulesPromise;
}

async function firebaseAuthClient() {
  if (firebaseAuthInstance) {
    return firebaseAuthInstance;
  }

  const [appModule, authModule] = await firebaseAuthModules();
  const response = await fetch("/auth/firebase-web-config");
  const data = await response.json();
  if (!response.ok || !data.ok) {
    throw new Error(data.error || "Google sign in is not configured.");
  }

  const app = appModule.initializeApp(data.config);
  firebaseAuthInstance = authModule.getAuth(app);
  return firebaseAuthInstance;
}

async function googleIdToken() {
  const [_appModule, authModule] = await firebaseAuthModules();
  const auth = await firebaseAuthClient();
  const provider = new authModule.GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  const result = await authModule.signInWithPopup(auth, provider);
  return result.user.getIdToken();
}

function googlePayload(button, idToken, extras = {}) {
  const payload = {
    idToken,
    role: button.dataset.role || "",
    classCode: button.dataset.classCode || "",
    inviteCode: button.dataset.inviteCode || "",
    ...extras,
  };
  return payload;
}

function setGoogleError(container, message) {
  const error = container?.querySelector("[data-google-auth-error]") || document.querySelector("[data-google-auth-error]");
  if (!error) {
    return;
  }
  error.textContent = message;
  error.hidden = !message;
}

async function submitGoogleAuth(button, idToken, extras = {}) {
  const response = await fetch(button.dataset.googleEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(googlePayload(button, idToken, extras)),
  });
  const data = await response.json();
  if (!response.ok || !data.ok) {
    if (data.needsName) {
      return data;
    }
    throw new Error(data.error || "Unable to continue with Google.");
  }
  window.location.href = data.redirect || "/";
  return data;
}

function openGoogleNameModal(button, idToken) {
  const modal = document.querySelector("[data-google-name-modal]");
  if (!modal) {
    return;
  }
  pendingGoogleNameRequest = { button, idToken };
  modal.hidden = false;
  modal.querySelector('input[name="google_first_name"]')?.focus();
}

function closeGoogleNameModal() {
  const modal = document.querySelector("[data-google-name-modal]");
  if (!modal) {
    return;
  }
  pendingGoogleNameRequest = null;
  modal.hidden = true;
  modal.querySelectorAll("input").forEach((input) => {
    input.value = "";
  });
}

document.querySelectorAll("[data-google-auth]").forEach((button) => {
  button.addEventListener("click", async () => {
    const container = button.closest(".auth-provider-stack");
    setGoogleError(container, "");
    button.disabled = true;
    const originalLabel = button.textContent;
    button.dataset.originalLabel = originalLabel;
    button.lastChild.textContent = "Opening Google...";

    try {
      const idToken = await googleIdToken();
      const data = await submitGoogleAuth(button, idToken);
      if (data?.needsName) {
        openGoogleNameModal(button, idToken);
      }
    } catch (error) {
      setGoogleError(container, error.message || "Unable to continue with Google.");
    } finally {
      button.disabled = false;
      if (!button.closest("[hidden]")) {
        button.lastChild.textContent = "Continue with Google";
      }
    }
  });
});

document.querySelector("[data-google-name-cancel]")?.addEventListener("click", closeGoogleNameModal);

document.querySelector("[data-google-name-submit]")?.addEventListener("click", async () => {
  const modal = document.querySelector("[data-google-name-modal]");
  const errorBox = modal?.querySelector("[data-google-name-error]");
  const firstName = modal?.querySelector('input[name="google_first_name"]')?.value.trim() || "";
  const lastName = modal?.querySelector('input[name="google_last_name"]')?.value.trim() || "";
  if (errorBox) {
    errorBox.hidden = true;
    errorBox.textContent = "";
  }
  if (!pendingGoogleNameRequest) {
    return;
  }
  if (!firstName || !lastName) {
    if (errorBox) {
      errorBox.textContent = "First and last name are required.";
      errorBox.hidden = false;
    }
    return;
  }
  try {
    await submitGoogleAuth(pendingGoogleNameRequest.button, pendingGoogleNameRequest.idToken, {
      firstName,
      lastName,
    });
  } catch (error) {
    if (errorBox) {
      errorBox.textContent = error.message || "Unable to finish Google signup.";
      errorBox.hidden = false;
    }
  }
});

function closeDropdown(dropdown) {
  const trigger = dropdown.querySelector(".custom-select-trigger");

  dropdown.classList.remove("is-open");
  trigger.setAttribute("aria-expanded", "false");
}

function closeOtherDropdowns(currentDropdown) {
  dropdowns.forEach((dropdown) => {
    if (dropdown !== currentDropdown) {
      closeDropdown(dropdown);
    }
  });
}

function openDropdown(dropdown) {
  const trigger = dropdown.querySelector(".custom-select-trigger");
  const selectedOption = dropdown.querySelector('.custom-option[aria-selected="true"]');

  closeOtherDropdowns(dropdown);
  dropdown.classList.add("is-open");
  trigger.setAttribute("aria-expanded", "true");

  if (selectedOption) {
    selectedOption.focus();
  }
}

function toggleDropdown(dropdown) {
  if (dropdown.classList.contains("is-open")) {
    closeDropdown(dropdown);
  } else {
    openDropdown(dropdown);
  }
}

function selectOption(dropdown, option) {
  const hiddenInput = dropdown.querySelector('input[type="hidden"]');
  const selectedLabel = dropdown.querySelector("[data-selected-label]");
  const trigger = dropdown.querySelector(".custom-select-trigger");
  const options = dropdown.querySelectorAll(".custom-option");
  const fieldName = hiddenInput.name;
  const labelText = option.textContent.trim();

  options.forEach((item) => item.setAttribute("aria-selected", "false"));
  option.setAttribute("aria-selected", "true");
  hiddenInput.value = option.dataset.value;
  selectedLabel.textContent = labelText;

  document.querySelectorAll(`input[name="${fieldName}"]`).forEach((input) => {
    input.value = option.dataset.value;
  });

  document.querySelectorAll(`[data-badge="${fieldName}"]`).forEach((badge) => {
    badge.textContent = labelText;
  });

  closeDropdown(dropdown);
  trigger.focus();

  if (fieldName === "unit") {
    updateTopicsForUnit(option);
    return;
  }

  if (fieldName === "topic") {
    submitPracticeConfig(dropdown);
  }
}

function submitPracticeConfig(dropdown) {
  const form = dropdown.closest("form");
  if (form) {
    form.submit();
  }
}

function updateTopicsForUnit(unitOption) {
  const form = unitOption.closest("form");
  const topicDropdown = form?.querySelector('[data-dropdown] input[name="topic"]')?.closest("[data-dropdown]");
  if (!topicDropdown || !unitOption.dataset.topics) {
    return;
  }

  const topics = JSON.parse(unitOption.dataset.topics);
  const topicHiddenInput = topicDropdown.querySelector('input[type="hidden"]');
  const topicSelectedLabel = topicDropdown.querySelector("[data-selected-label]");
  const topicOptions = topicDropdown.querySelector(".custom-options");

  topicOptions.innerHTML = topics.map(([value, label], index) => `
            <button
              class="custom-option"
              id="topic-option-${index}"
              role="option"
              type="button"
              data-value="${value}"
              aria-selected="${index === 0 ? "true" : "false"}"
              tabindex="-1"
            >${label}</button>`).join("");

  topicHiddenInput.value = topics[0][0];
  topicSelectedLabel.textContent = topics[0][1];

  document.querySelectorAll('input[name="topic"]').forEach((input) => {
    input.value = topics[0][0];
  });

  document.querySelectorAll('[data-badge="topic"]').forEach((badge) => {
    badge.textContent = topics[0][1];
  });

  bindDropdownOptions(topicDropdown);
  selectOption(topicDropdown, topicOptions.querySelector(".custom-option"));
}

function moveFocus(dropdown, direction) {
  const options = Array.from(dropdown.querySelectorAll(".custom-option"));
  const currentIndex = options.indexOf(document.activeElement);
  const nextIndex = currentIndex === -1
    ? 0
    : (currentIndex + direction + options.length) % options.length;

  options[nextIndex].focus();
}

function bindDropdownOptions(dropdown) {
  const trigger = dropdown.querySelector(".custom-select-trigger");
  const options = dropdown.querySelectorAll(".custom-option");

  options.forEach((option) => {
    option.addEventListener("click", () => {
      selectOption(dropdown, option);
    });

    option.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectOption(dropdown, option);
      }

      if (event.key === "ArrowDown") {
        event.preventDefault();
        moveFocus(dropdown, 1);
      }

      if (event.key === "ArrowUp") {
        event.preventDefault();
        moveFocus(dropdown, -1);
      }

      if (event.key === "Escape") {
        closeDropdown(dropdown);
        trigger.focus();
      }
    });
  });
}

dropdowns.forEach((dropdown) => {
  const trigger = dropdown.querySelector(".custom-select-trigger");

  trigger.addEventListener("click", () => {
    toggleDropdown(dropdown);
  });

  trigger.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      toggleDropdown(dropdown);
    }

    if (event.key === "ArrowDown") {
      event.preventDefault();
      openDropdown(dropdown);
    }

    if (event.key === "Escape") {
      closeDropdown(dropdown);
    }
  });

  bindDropdownOptions(dropdown);
});

document.addEventListener("click", (event) => {
  dropdowns.forEach((dropdown) => {
    if (!dropdown.contains(event.target)) {
      closeDropdown(dropdown);
    }
  });
});

document.querySelectorAll("[data-question-view-group]").forEach((group) => {
  group.addEventListener("change", (event) => {
    if (!event.target.matches("[data-question-view]")) {
      return;
    }

    const checkboxes = Array.from(group.querySelectorAll("[data-question-view]"));
    if (!checkboxes.some((checkbox) => checkbox.checked)) {
      event.target.checked = true;
      return;
    }

    submitPracticeConfig(group);
  });
});

document.querySelectorAll("[data-config-checkbox-group]").forEach((group) => {
  group.addEventListener("change", (event) => {
    if (!event.target.matches("[data-config-checkbox]")) {
      return;
    }

    const checkboxes = Array.from(group.querySelectorAll("[data-config-checkbox]"));
    if (!checkboxes.some((checkbox) => checkbox.checked)) {
      event.target.checked = true;
      return;
    }

    submitPracticeConfig(group);
  });
});

function replaceHiddenFieldValues(form, fieldName, values) {
  Array.from(form.elements).forEach((element) => {
    if (element.type === "hidden" && element.name === fieldName) {
      element.remove();
    }
  });

  values.forEach((value) => {
    const input = document.createElement("input");
    input.type = "hidden";
    input.name = fieldName;
    input.value = value;
    form.appendChild(input);
  });
}

function syncConfigCheckboxesToForm(form) {
  document.querySelectorAll("[data-config-checkbox-group]").forEach((group) => {
    const checkboxes = Array.from(group.querySelectorAll("[data-config-checkbox]"));
    if (!checkboxes.length) {
      return;
    }

    const fieldName = checkboxes[0].name;
    const values = checkboxes
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.value);
    replaceHiddenFieldValues(form, fieldName, values);
  });
}

document.querySelectorAll(".answer-panel").forEach((form) => {
  form.addEventListener("submit", (event) => {
    const action = event.submitter?.value;
    if (action !== "skip" && action !== "next") {
      return;
    }

    document.querySelectorAll("[data-question-view]").forEach((checkbox) => {
      form
        .querySelectorAll(`input[type="hidden"][name="${checkbox.name}"]`)
        .forEach((input) => {
          input.value = checkbox.checked ? "true" : "";
        });
    });

    syncConfigCheckboxesToForm(form);
  });
});

let currentAnswerInput = null;

document.addEventListener("focusin", (event) => {
  if (event.target.matches(".answer-panel input[type='text']")) {
    currentAnswerInput = event.target;
  }
});

function insertAtCursor(input, value) {
  const start = input.selectionStart ?? input.value.length;
  const end = input.selectionEnd ?? input.value.length;

  input.value = `${input.value.slice(0, start)}${value}${input.value.slice(end)}`;
  input.focus();
  input.setSelectionRange(start + value.length, start + value.length);
}

document.querySelectorAll("[data-answer-helper]").forEach((button) => {
  button.addEventListener("mousedown", (event) => {
    event.preventDefault();
  });

  button.addEventListener("click", () => {
    const input = button.closest(".answer-field")?.querySelector("input[type='text']")
      || currentAnswerInput
      || button.closest(".answer-row")?.querySelector("input[type='text']");
    if (input) {
      insertAtCursor(input, button.dataset.answerHelper);
    }
  });
});

const testModal = document.querySelector("[data-test-modal]");

function openTestModal() {
  if (!testModal) {
    return;
  }
  testModal.classList.add("is-open");
  testModal.setAttribute("aria-hidden", "false");
  testModal.querySelector("select, input, button")?.focus();
}

function closeTestModal() {
  if (!testModal) {
    return;
  }
  testModal.classList.remove("is-open");
  testModal.setAttribute("aria-hidden", "true");
}

function selectedTestTopicValues() {
  return Array.from(document.querySelectorAll('[data-test-topic-inputs] input[name="test_topics"]'))
    .map((input) => input.value);
}

function syncPrimaryTestTopic() {
  const first = selectedTestTopicValues()[0];
  const unitInput = document.querySelector("[data-test-primary-unit]");
  const topicInput = document.querySelector("[data-test-primary-topic]");
  if (!first || !unitInput || !topicInput) {
    return;
  }
  const [unit, topic] = first.split("|");
  unitInput.value = unit;
  topicInput.value = topic;
}

function addTestTopicInput(value) {
  const holder = document.querySelector("[data-test-topic-inputs]");
  if (!holder || selectedTestTopicValues().includes(value)) {
    return;
  }
  const input = document.createElement("input");
  input.type = "hidden";
  input.name = "test_topics";
  input.value = value;
  holder.appendChild(input);
}

function removeTestTopicInput(value) {
  const inputs = Array.from(document.querySelectorAll('[data-test-topic-inputs] input[name="test_topics"]'));
  if (inputs.length <= 1) {
    return;
  }
  inputs.forEach((input) => {
    if (input.value === value) {
      input.remove();
    }
  });
}

function updateTopicPickerAddedStates() {
  const selected = new Set(selectedTestTopicValues());
  document.querySelectorAll("[data-topic-picker-topic]").forEach((button) => {
    const value = `${button.dataset.unit}|${button.dataset.topicPickerTopic}`;
    button.classList.toggle("is-added", selected.has(value));
  });
}

function closeTopicPicker(picker) {
  const menu = picker?.querySelector("[data-topic-picker-menu]");
  const units = picker?.querySelector("[data-topic-picker-units]");
  const back = picker?.querySelector("[data-topic-picker-back]");
  const title = picker?.querySelector("[data-topic-picker-title]");
  if (!menu || !units || !back || !title) {
    return;
  }
  menu.hidden = true;
  menu.classList.remove("align-right", "drop-up");
  units.hidden = false;
  back.hidden = true;
  title.textContent = "Select a unit";
  picker.querySelectorAll("[data-topic-picker-panel]").forEach((panel) => {
    panel.classList.remove("is-active");
  });
}

function positionTopicPickerMenu(picker) {
  const menu = picker?.querySelector("[data-topic-picker-menu]");
  const dialog = picker?.closest(".test-dialog");
  if (!menu || !dialog || menu.hidden) {
    return;
  }

  menu.classList.remove("align-right", "drop-up");
  const dialogRect = dialog.getBoundingClientRect();
  let menuRect = menu.getBoundingClientRect();

  if (menuRect.right > dialogRect.right - 12) {
    menu.classList.add("align-right");
    menuRect = menu.getBoundingClientRect();
  }

  if (menuRect.left < dialogRect.left + 12) {
    menu.classList.remove("align-right");
    menuRect = menu.getBoundingClientRect();
  }

  if (menuRect.bottom > dialogRect.bottom - 12) {
    menu.classList.add("drop-up");
  }
}

function initializeTopicPicker() {
  document.querySelectorAll("[data-topic-picker]").forEach((picker) => {
    const trigger = picker.querySelector("[data-topic-picker-trigger]");
    const menu = picker.querySelector("[data-topic-picker-menu]");
    const units = picker.querySelector("[data-topic-picker-units]");
    const back = picker.querySelector("[data-topic-picker-back]");
    const title = picker.querySelector("[data-topic-picker-title]");
    if (!trigger || !menu || !units || !back || !title) {
      return;
    }

    trigger.addEventListener("click", () => {
      const nextOpen = menu.hidden;
      document.querySelectorAll("[data-topic-picker]").forEach(closeTopicPicker);
      menu.hidden = !nextOpen;
      updateTopicPickerAddedStates();
      positionTopicPickerMenu(picker);
    });

    picker.querySelectorAll("[data-topic-picker-unit]").forEach((button) => {
      button.addEventListener("click", () => {
        units.hidden = true;
        back.hidden = false;
        title.textContent = button.textContent.trim().replace(/^Unit \\d+:\\s*/, "");
        picker.querySelectorAll("[data-topic-picker-panel]").forEach((panel) => {
          panel.classList.toggle("is-active", panel.dataset.topicPickerPanel === button.dataset.topicPickerUnit);
        });
        positionTopicPickerMenu(picker);
      });
    });

    back.addEventListener("click", () => {
      units.hidden = false;
      back.hidden = true;
      title.textContent = "Select a unit";
      picker.querySelectorAll("[data-topic-picker-panel]").forEach((panel) => {
        panel.classList.remove("is-active");
      });
      positionTopicPickerMenu(picker);
    });

    picker.querySelectorAll("[data-topic-picker-topic]").forEach((button) => {
      button.addEventListener("click", () => {
        const value = `${button.dataset.unit}|${button.dataset.topicPickerTopic}`;
        addTestTopicInput(value);
        const chip = document.createElement("span");
        chip.className = "selected-topic-chip";
        chip.dataset.testTopicChip = "";
        chip.dataset.value = value;
        chip.innerHTML = `${button.dataset.label}<button type="button" data-remove-test-topic aria-label="Remove ${button.dataset.label}">×</button>`;
        picker.parentElement.insertBefore(chip, picker);
        syncPrimaryTestTopic();
        updateTopicPickerAddedStates();
        closeTopicPicker(picker);
      });
    });
  });
}

document.addEventListener("click", (event) => {
  if (event.target.matches("[data-remove-test-topic]")) {
    const chip = event.target.closest("[data-test-topic-chip]");
    if (chip && selectedTestTopicValues().length > 1) {
      removeTestTopicInput(chip.dataset.value);
      chip.remove();
      syncPrimaryTestTopic();
      updateTopicPickerAddedStates();
    }
    return;
  }

  document.querySelectorAll("[data-topic-picker]").forEach((picker) => {
    if (!picker.contains(event.target)) {
      closeTopicPicker(picker);
    }
  });
});

function updateTimerModeUI() {
  const checked = document.querySelector('input[name="test_timer_mode"]:checked');
  const timeLimitField = document.querySelector("[data-time-limit-field]");
  document.querySelectorAll(".timer-option").forEach((label) => {
    const input = label.querySelector('input[name="test_timer_mode"]');
    label.classList.toggle("is-selected", input?.checked);
  });
  if (timeLimitField && checked) {
    timeLimitField.hidden = checked.value !== "countdown";
  }
}

document.querySelectorAll('input[name="test_timer_mode"]').forEach((input) => {
  input.addEventListener("change", updateTimerModeUI);
});

document.querySelectorAll("[data-open-test-modal]").forEach((button) => {
  button.addEventListener("click", openTestModal);
});

document.querySelectorAll("[data-close-test-modal]").forEach((button) => {
  button.addEventListener("click", closeTestModal);
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeTestModal();
  }
});

function formatTimer(seconds) {
  const safeSeconds = Math.max(0, seconds);
  const minutes = String(Math.floor(safeSeconds / 60)).padStart(2, "0");
  const remainder = String(safeSeconds % 60).padStart(2, "0");
  return `${minutes}:${remainder}`;
}

const testTimer = document.querySelector("[data-test-timer]");
let currentElapsed = Number(testTimer?.dataset.initialElapsed || "0");

function syncElapsedInputs() {
  document.querySelectorAll("[data-test-elapsed-input]").forEach((input) => {
    input.value = String(currentElapsed);
  });
}

if (testTimer) {
  const output = document.querySelector("[data-test-time]");
  const mode = testTimer.dataset.timerMode || "stopwatch";
  const limitMinutes = Number(testTimer.dataset.timeLimit || "30");

  syncElapsedInputs();
  window.setInterval(() => {
    currentElapsed += 1;
    const remaining = Math.max(0, limitMinutes * 60 - currentElapsed);
    if (output) {
      output.textContent = formatTimer(mode === "countdown" ? remaining : currentElapsed);
    }
    syncElapsedInputs();
  }, 1000);
}

document.querySelectorAll("form").forEach((form) => {
  form.addEventListener("submit", syncElapsedInputs);
});

initializeTopicPicker();
updateTopicPickerAddedStates();
syncPrimaryTestTopic();
updateTimerModeUI();

document.querySelectorAll("[data-profile-menu]").forEach((menu) => {
  const trigger = menu.querySelector("[data-profile-trigger]");
  const dropdown = menu.querySelector("[data-profile-dropdown]");
  if (!trigger || !dropdown) {
    return;
  }

  trigger.addEventListener("click", () => {
    const willOpen = dropdown.hidden;
    document.querySelectorAll("[data-profile-dropdown]").forEach((other) => {
      other.hidden = true;
    });
    dropdown.hidden = !willOpen;
  });

  document.addEventListener("click", (event) => {
    if (!menu.contains(event.target)) {
      dropdown.hidden = true;
    }
  });
});

document.querySelectorAll(".code-input").forEach((input) => {
  input.addEventListener("input", () => {
    input.value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6);
  });
});

function openCodeModal(type) {
  const modal = document.querySelector(`[data-code-modal="${type}"]`);
  if (!modal) {
    return;
  }
  modal.hidden = false;
  modal.querySelector("input, button")?.focus();
}

function closeCodeModal(modal) {
  if (!modal) {
    return;
  }
  modal.hidden = true;
}

document.querySelectorAll("[data-open-code-modal]").forEach((button) => {
  button.addEventListener("click", () => openCodeModal(button.dataset.openCodeModal));
});

document.querySelectorAll("[data-close-code-modal]").forEach((button) => {
  button.addEventListener("click", () => closeCodeModal(button.closest("[data-code-modal]")));
});

document.querySelectorAll("[data-code-modal]").forEach((modal) => {
  modal.addEventListener("click", (event) => {
    if (event.target.matches(".code-modal-backdrop")) {
      closeCodeModal(modal);
    }
  });
});

document.querySelectorAll("[data-code-form]").forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const generateButton = form.querySelector("[data-generate-code]");
    const errorBox = form.querySelector("[data-code-error]");
    const codeBox = form.querySelector("[data-generated-code-box]");
    const codeValue = form.querySelector("[data-generated-code]");
    const copyButton = form.querySelector("[data-copy-code]");

    if (errorBox) {
      errorBox.hidden = true;
      errorBox.textContent = "";
    }
    if (generateButton) {
      generateButton.disabled = true;
      generateButton.textContent = "Generating...";
    }

    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "X-Requested-With": "fetch" },
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Unable to generate code.");
      }
      if (codeValue) {
        codeValue.textContent = data.code;
      }
      if (codeBox) {
        codeBox.hidden = false;
      }
      if (copyButton) {
        copyButton.hidden = false;
        copyButton.textContent = "Copy";
      }
      if (generateButton) {
        generateButton.textContent = "Regenerate";
      }
    } catch (error) {
      if (errorBox) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
      }
      if (generateButton) {
        generateButton.textContent = "Generate";
      }
    } finally {
      if (generateButton) {
        generateButton.disabled = false;
      }
    }
  });
});

document.querySelectorAll("[data-copy-code]").forEach((button) => {
  button.addEventListener("click", async () => {
    const dialog = button.closest("[data-code-modal]");
    const code = dialog?.querySelector("[data-generated-code]")?.textContent?.trim();
    if (!code) {
      return;
    }
    try {
      await navigator.clipboard.writeText(code);
      button.textContent = "Copied";
      window.setTimeout(() => {
        button.textContent = "Copy";
      }, 1600);
    } catch (_error) {
      button.textContent = code;
    }
  });
});

function miloAvatarSvg(emotion = "greeting", size = 64, animate = false) {
  const tilts = {
    greeting: 0,
    thinking: -8,
    encouraging: 3,
    celebrating: 6,
    explaining: 0,
    confused: -12,
    great: 5,
    reading: -4,
  };
  const safeEmotion = Object.prototype.hasOwnProperty.call(tilts, emotion) ? emotion : "greeting";
  const tilt = tilts[safeEmotion];
  const animationClass = animate ? " milo-float" : "";
  const showSparkles = safeEmotion === "celebrating" || safeEmotion === "great";
  const showQuestion = safeEmotion === "confused";
  const showThought = safeEmotion === "thinking" || safeEmotion === "reading";

  return `<svg class="milo-avatar-svg${animationClass}" viewBox="0 0 100 130" width="${size}" height="${Math.round(size * 1.3)}" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <g transform="rotate(${tilt}, 50, 80)">
      <ellipse cx="50" cy="122" rx="26" ry="5" fill="#111118" fill-opacity="0.12"/>
      <rect x="14" y="48" width="72" height="68" rx="16" fill="#111118"/>
      <text x="50" y="97" text-anchor="middle" font-family="system-ui,sans-serif" font-size="28" font-weight="800" fill="white" fill-opacity="0.9">M</text>
      <rect x="22" y="32" width="56" height="10" rx="3" fill="#111118"/>
      <rect x="32" y="18" width="36" height="18" rx="5" fill="#1a1a24"/>
      <line x1="72" y1="37" x2="80" y2="52" stroke="#111118" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="80" cy="55" r="4.5" fill="#111118"/>
      <rect x="2" y="68" width="16" height="10" rx="5" fill="#111118"/>
      <rect x="82" y="68" width="16" height="10" rx="5" fill="#111118"/>
      <rect x="24" y="112" width="18" height="12" rx="6" fill="#111118"/>
      <rect x="58" y="112" width="18" height="12" rx="6" fill="#111118"/>
    </g>
    ${showSparkles ? `<text x="8" y="40" font-size="14" fill="#FFD700">✦</text><text x="78" y="32" font-size="10" fill="#FFD700">✦</text><text x="82" y="55" font-size="8" fill="#FFD700">✧</text>` : ""}
    ${showQuestion ? `<text x="78" y="38" font-size="18" font-weight="bold" fill="#5B5FD9" font-family="Georgia,serif">?</text>` : ""}
    ${showThought ? `<circle cx="80" cy="52" r="3.5" fill="#d0d0e0" fill-opacity="0.7"/><circle cx="87" cy="44" r="5" fill="#d0d0e0" fill-opacity="0.7"/><circle cx="92" cy="35" r="7" fill="#d0d0e0" fill-opacity="0.7"/>` : ""}
  </svg>`;
}

function initializeMiloChat() {
  const root = document.querySelector("[data-milo]");
  if (!root) {
    return;
  }

  const openButton = root.querySelector("[data-milo-open]");
  const closeButton = root.querySelector("[data-milo-close]");
  const nudge = root.querySelector("[data-milo-nudge]");
  const panel = root.querySelector("[data-milo-panel]");
  const appFrame = root.closest(".app-frame");
  const answerForm = document.querySelector(".answer-panel");
  const form = root.querySelector("[data-milo-form]");
  const input = root.querySelector("[data-milo-input]");
  const sendButton = root.querySelector("[data-milo-send]");
  const messages = root.querySelector("[data-milo-messages]");
  const avatar = root.querySelector("[data-milo-avatar]");
  const emotionLabel = root.querySelector("[data-milo-emotion]");
  const quickActions = root.querySelectorAll("[data-milo-quick]");
  const answerHelpStatus = document.querySelector('.answer-panel input[name="problem_help_status"]');
  const miloOpenStorageKey = "mathpracai:milo-open";
  const miloOpenProblemStorageKey = "mathpracai:milo-open-problem";
  const miloNudgeArmedStorageKey = "mathpracai:milo-nudge-armed";
  const miloNudgeDismissedProblemStorageKey = "mathpracai:milo-nudge-dismissed-problem";
  const miloNudgeDismissedAttemptStorageKey = "mathpracai:milo-nudge-dismissed-attempts";
  let thinkingRow = null;
  let sending = false;

  function baseContext() {
    try {
      return JSON.parse(root.dataset.miloContext || "{}");
    } catch (_error) {
      return {};
    }
  }

  function setEmotion(emotion) {
    if (avatar) {
      avatar.innerHTML = miloAvatarSvg(emotion, 72, true);
    }
    if (emotionLabel) {
      emotionLabel.textContent = emotion;
    }
  }

  function scrollToBottom() {
    if (messages) {
      messages.scrollTop = messages.scrollHeight;
    }
  }

  function persistOpenState(isOpen) {
    try {
      window.sessionStorage.setItem(miloOpenStorageKey, isOpen ? "true" : "false");
    } catch (_error) {
      // The visual state should still work if browser storage is unavailable.
    }
  }

  function storedOpenState() {
    try {
      return window.sessionStorage.getItem(miloOpenStorageKey) === "true";
    } catch (_error) {
      return false;
    }
  }

  function storedOpenProblemKey() {
    try {
      return window.sessionStorage.getItem(miloOpenProblemStorageKey) || "";
    } catch (_error) {
      return "";
    }
  }

  function persistOpenProblemKey() {
    try {
      window.sessionStorage.setItem(miloOpenProblemStorageKey, currentProblemStorageKey());
    } catch (_error) {
      // The visual state should still work if browser storage is unavailable.
    }
  }

  function persistedNudgeArmed() {
    try {
      return window.sessionStorage.getItem(miloNudgeArmedStorageKey) === "true";
    } catch (_error) {
      return false;
    }
  }

  function persistNudgeArmed(isArmed) {
    try {
      window.sessionStorage.setItem(miloNudgeArmedStorageKey, isArmed ? "true" : "false");
    } catch (_error) {
      // The visual state should still work if browser storage is unavailable.
    }
  }

  function storedNudgeDismissedProblemKey() {
    try {
      return window.sessionStorage.getItem(miloNudgeDismissedProblemStorageKey) || "";
    } catch (_error) {
      return "";
    }
  }

  function storedNudgeDismissedAttemptCount() {
    try {
      return Number(window.sessionStorage.getItem(miloNudgeDismissedAttemptStorageKey) || "0");
    } catch (_error) {
      return 0;
    }
  }

  function persistNudgeDismissedState(problemKey, attemptCount) {
    try {
      window.sessionStorage.setItem(miloNudgeDismissedProblemStorageKey, problemKey);
      window.sessionStorage.setItem(miloNudgeDismissedAttemptStorageKey, String(attemptCount));
    } catch (_error) {
      // The visual state should still work if browser storage is unavailable.
    }
  }

  function setMiloOpen(isOpen, persist = true, animate = false) {
    if (panel) {
      panel.hidden = !isOpen;
      panel.classList.toggle("milo-chat-open", isOpen && animate);
    }
    if (openButton) {
      openButton.hidden = isOpen;
      openButton.setAttribute("aria-expanded", isOpen ? "true" : "false");
    }
    appFrame?.classList.toggle("milo-is-open", isOpen);
    if (persist) {
      persistOpenState(isOpen);
    }
    if (isOpen) {
      persistOpenProblemKey();
      persistNudgeArmed(false);
      persistNudgeDismissedState(currentProblemIdentity(), currentAttemptCount());
      updateNudgeVisibility();
      window.setTimeout(() => input?.focus(), 250);
      return;
    }
    updateNudgeVisibility();
  }

  function storageHash(value) {
    let hash = 0;
    for (let index = 0; index < value.length; index += 1) {
      hash = ((hash << 5) - hash + value.charCodeAt(index)) | 0;
    }
    return Math.abs(hash).toString(36);
  }

  function currentProblemIdentity() {
    const context = baseContext();
    const problem = context.problem || {};
    return [
      context.unit || "",
      context.topic || "",
      problem.problem_type || "",
      problem.question || "",
      problem.officialAnswer || "",
    ].join("|");
  }

  function currentProblemStorageKey() {
    return `mathpracai:milo-chat:${storageHash(currentProblemIdentity())}`;
  }

  function currentAttemptCount() {
    const context = baseContext();
    if (Number.isFinite(Number(context.attemptCount))) {
      return Number(context.attemptCount);
    }
    if (Array.isArray(context.curAttempt)) {
      return context.curAttempt.length;
    }
    return 0;
  }

  function currentProblemWrongAttemptEligible() {
    const attempts = currentAttemptCount();
    if (attempts < 1) {
      return false;
    }
    const dismissedProblemKey = storedNudgeDismissedProblemKey();
    if (dismissedProblemKey !== currentProblemIdentity()) {
      return true;
    }
    return attempts > storedNudgeDismissedAttemptCount();
  }

  function syncNudgeArmedState() {
    if (persistedNudgeArmed()) {
      return true;
    }
    if (!currentProblemWrongAttemptEligible()) {
      return false;
    }
    persistNudgeArmed(true);
    return true;
  }

  function updateNudgeVisibility() {
    if (!nudge) {
      return;
    }
    const shouldShow = (panel?.hidden ?? true) && syncNudgeArmedState();
    nudge.hidden = !shouldShow;
  }

  function hiddenField(name) {
    return answerForm?.querySelector(`input[type="hidden"][name="${name}"]`) || null;
  }

  function answerTextInputs() {
    return Array.from(answerForm?.querySelectorAll('input[type="text"][name]') || []);
  }

  function currentAnswerValues() {
    const values = {};
    answerTextInputs().forEach((field) => {
      values[field.name] = field.value;
    });
    return values;
  }

  function answerButtons() {
    return Array.from(answerForm?.querySelectorAll('button[name="action"]') || []);
  }

  function secondaryActionButtons() {
    return Array.from(answerForm?.querySelectorAll('.secondary-actions button[name="action"]') || []);
  }

  function primaryActionButton() {
    return answerForm?.querySelector('.btn.btn-accent[name="action"]') || null;
  }

  function setPracticeButtonsDisabled(disabled) {
    answerButtons().forEach((button) => {
      button.disabled = disabled || button.disabled;
    });
  }

  function setHiddenValue(name, value) {
    const field = hiddenField(name);
    if (field) {
      field.value = value;
    }
  }

  function updateStatCount(selector, nextValue) {
    const stat = document.querySelector(selector);
    if (!stat) {
      return;
    }
    const label = stat.textContent.split(":")[0] || stat.textContent;
    stat.textContent = `${label}: ${nextValue}`;
  }

  function restorePracticeButtons() {
    if (!answerForm) {
      return;
    }
    const hintVisible = hiddenField("hint_visible")?.value === "true";
    const solutionVisible = hiddenField("solution_visible")?.value === "true";
    const feedbackType = document.querySelector(".feedback.correct") ? "correct" : "";
    const hintButton = answerForm.querySelector('button[name="action"][value="hint"]');
    const solutionButton = answerForm.querySelector('button[name="action"][value="solution"]');
    const skipButton = answerForm.querySelector('button[name="action"][value="skip"]');
    if (hintButton) {
      hintButton.disabled = hintVisible || solutionVisible || feedbackType === "correct";
    }
    if (solutionButton) {
      solutionButton.disabled = solutionVisible || feedbackType === "correct";
    }
    if (skipButton) {
      skipButton.disabled = solutionVisible || feedbackType === "correct";
    }
    syncPrimaryActionButton();
  }

  function syncPrimaryActionButton() {
    const primaryButton = primaryActionButton();
    if (!primaryButton) {
      return;
    }
    const solutionVisible = hiddenField("solution_visible")?.value === "true";
    const feedbackType = document.querySelector(".feedback.correct") ? "correct" : "";
    if (solutionVisible || feedbackType === "correct") {
      primaryButton.value = "next";
      primaryButton.innerHTML = 'Next Problem<svg class="ui-icon" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"></path><path d="m12 5 7 7-7 7"></path></svg>';
    } else {
      primaryButton.value = "check";
      primaryButton.textContent = "Check Answer";
    }
    primaryButton.disabled = false;
  }

  function showPrimaryLoading() {
    const primaryButton = primaryActionButton();
    if (!primaryButton) {
      return;
    }
    primaryButton.dataset.loading = "true";
    primaryButton.setAttribute("aria-disabled", "true");
    primaryButton.innerHTML = '<span class="btn-loading-dots" aria-label="Loading"><span></span><span></span><span></span></span>';
  }

  function hidePrimaryLoading() {
    const primaryButton = primaryActionButton();
    if (primaryButton) {
      delete primaryButton.dataset.loading;
      primaryButton.removeAttribute("aria-disabled");
    }
    syncPrimaryActionButton();
  }

  function ensureHelpBox(type) {
    if (!answerForm) {
      return null;
    }
    let stack = answerForm.querySelector("[data-help-stack]");
    if (!stack) {
      const answerCard = answerForm.querySelector(".answer-card");
      if (!answerCard) {
        return null;
      }
      stack = document.createElement("div");
      stack.className = "help-stack";
      stack.dataset.helpStack = "";
      const utilityRow = answerCard.querySelector(".utility-row");
      answerCard.insertBefore(stack, utilityRow || null);
    }
    let box = stack.querySelector(`[data-help-box="${type}"]`);
    if (!box) {
      box = document.createElement("div");
      box.className = `help-box ${type === "hint" ? "hint-box" : "solution-box"}`;
      box.dataset.helpBox = type;
      stack.appendChild(box);
    }
    return box;
  }

  function setHelpBoxText(type, text) {
    const box = ensureHelpBox(type);
    if (box) {
      box.textContent = text;
    }
  }

  function lockAnswerInputs() {
    answerTextInputs().forEach((field) => {
      field.disabled = true;
    });
    answerForm?.querySelectorAll("[data-answer-helper]").forEach((button) => {
      button.disabled = true;
    });
  }

  function buildActionContext(actionMode) {
    const context = baseContext();
    context.actionMode = actionMode;
    context.currentAnswers = currentAnswerValues();
    context.activeRepresentation = hiddenField("active_question_view")?.value || context.activeRepresentation || "";
    context.helpStatus = answerHelpStatus?.value || context.helpStatus || "none";
    return context;
  }

  function applyHintClientState(reply) {
    setHelpBoxText("hint", reply);
    setHiddenValue("milo_hint_text", reply);
    setHiddenValue("hint_visible", "true");
    if (answerHelpStatus && answerHelpStatus.value !== "solution") {
      answerHelpStatus.value = "hint";
    }
    const problemCounted = hiddenField("problem_counted");
    if (problemCounted && problemCounted.value !== "true") {
      const hintCountField = hiddenField("hint_count");
      const nextCount = Number(hintCountField?.value || "0") + 1;
      if (hintCountField) {
        hintCountField.value = String(nextCount);
      }
      problemCounted.value = "true";
      updateStatCount(".stat-hints", nextCount);
      const testHintsField = hiddenField("test_hints");
      if (testHintsField) {
        testHintsField.value = String(Number(testHintsField.value || "0") + 1);
      }
    }
    hidePrimaryLoading();
    restorePracticeButtons();
  }

  function applySolutionClientState(reply) {
    setHelpBoxText("solution", reply);
    setHiddenValue("milo_solution_text", reply);
    setHiddenValue("solution_visible", "true");
    setHiddenValue("answered", "true");
    if (answerHelpStatus) {
      answerHelpStatus.value = "solution";
    }
    const problemCounted = hiddenField("problem_counted");
    if (problemCounted && problemCounted.value !== "true") {
      const solvedCountField = hiddenField("solved_count");
      const nextCount = Number(solvedCountField?.value || "0") + 1;
      if (solvedCountField) {
        solvedCountField.value = String(nextCount);
      }
      problemCounted.value = "true";
      updateStatCount(".stat-solved", nextCount);
    }
    lockAnswerInputs();
    hidePrimaryLoading();
    restorePracticeButtons();
  }

  async function sendMiloAction(actionMode) {
    if (!answerForm) {
      return;
    }
    const endpoint = actionMode === "solution" ? "/milo/solution" : "/milo/hint";
    setPracticeButtonsDisabled(true);
    showPrimaryLoading();
    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(buildActionContext(actionMode)),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Milo is having trouble right now. Try again in a moment.");
      }
      const reply = (data.reply || "").trim() || "Milo is having trouble right now. Try again in a moment.";
      if (actionMode === "solution") {
        applySolutionClientState(reply);
      } else {
        applyHintClientState(reply);
      }
    } catch (error) {
      const fallback = error.message || "Milo is having trouble right now. Try again in a moment.";
      setHelpBoxText(actionMode === "solution" ? "solution" : "hint", fallback);
    } finally {
      hidePrimaryLoading();
      restorePracticeButtons();
    }
  }

  function currentMessages() {
    return Array.from(messages?.querySelectorAll(".milo-message-row") || []).map((row) => ({
      from: row.classList.contains("is-student") ? "student" : "milo",
      text: row.textContent.trim(),
    })).filter((turn) => turn.text);
  }

  function persistMessages() {
    try {
      window.sessionStorage.setItem(currentProblemStorageKey(), JSON.stringify(currentMessages()));
    } catch (_error) {
      // Chat persistence is helpful, but the tutor should still work if storage is unavailable.
    }
  }

  function restoreMessages() {
    if (!messages) {
      return;
    }
    let storedMessages = null;
    try {
      storedMessages = JSON.parse(window.sessionStorage.getItem(currentProblemStorageKey()) || "null");
    } catch (_error) {
      storedMessages = null;
    }
    if (!Array.isArray(storedMessages) || !storedMessages.length) {
      return;
    }
    messages.innerHTML = "";
    storedMessages.forEach((turn) => {
      if (turn && typeof turn.text === "string") {
        appendMessage(turn.from === "student" ? "student" : "milo", turn.text, false);
      }
    });
    scrollToBottom();
  }

  function appendMessage(from, text, shouldPersist = true) {
    if (!messages) {
      return;
    }
    const row = document.createElement("div");
    row.className = `milo-message-row milo-msg-in ${from === "student" ? "is-student" : "is-milo"}`;
    const bubble = document.createElement("div");
    bubble.className = "milo-message";
    bubble.textContent = text;
    row.appendChild(bubble);
    messages.appendChild(row);
    scrollToBottom();
    if (shouldPersist) {
      persistMessages();
    }
  }

  function showThinking() {
    if (!messages || thinkingRow) {
      return;
    }
    thinkingRow = document.createElement("div");
    thinkingRow.className = "milo-message-row milo-msg-in is-milo";
    thinkingRow.innerHTML = `<div class="milo-message milo-thinking-dots"><span class="milo-think-1"></span><span class="milo-think-2"></span><span class="milo-think-3"></span></div>`;
    messages.appendChild(thinkingRow);
    scrollToBottom();
  }

  function hideThinking() {
    thinkingRow?.remove();
    thinkingRow = null;
  }

  function setSending(nextSending) {
    sending = nextSending;
    if (sendButton) {
      sendButton.disabled = sending || !input?.value.trim();
    }
    quickActions.forEach((button) => {
      button.disabled = sending;
    });
  }

  function markMiloHelpStatus(helpStatus) {
    if (!answerHelpStatus) {
      return;
    }
    if (helpStatus === "solution") {
      answerHelpStatus.value = "solution";
      return;
    }
    if (answerHelpStatus.value !== "solution") {
      answerHelpStatus.value = "hint";
    }
  }

  function chatHistoryForRequest() {
    return Array.from(messages?.querySelectorAll(".milo-message-row") || []).map((row) => ({
      role: row.classList.contains("is-student") ? "student" : "assistant",
      message: row.textContent.trim(),
    })).filter((turn) => turn.message);
  }

  async function sendMiloMessage(text) {
    const message = text.trim();
    if (!message || sending) {
      return;
    }

    appendMessage("student", message);
    if (input) {
      input.value = "";
    }
    setEmotion("thinking");
    showThinking();
    setSending(true);
    markMiloHelpStatus("hint");

    const context = baseContext();
    context.studentMessage = message;
    context.chatHistory = chatHistoryForRequest();
    context.helpStatus = answerHelpStatus?.value || context.helpStatus || "hint";

    try {
      const response = await fetch("/ai-tutor/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(context),
      });
      const data = await response.json();
      if (!response.ok || !data.ok) {
        throw new Error(data.error || "Milo could not respond right now.");
      }
      hideThinking();
      setEmotion("explaining");
      const replyMessages = Array.isArray(data.replyMessages) && data.replyMessages.length
        ? data.replyMessages
        : [data.reply || "Let's keep working through this step by step."];
      replyMessages.forEach((replyText, index) => {
        window.setTimeout(() => {
          appendMessage("milo", replyText);
        }, index * 320);
      });
      markMiloHelpStatus(data.helpStatus || "hint");
    } catch (error) {
      hideThinking();
      setEmotion("confused");
      appendMessage("milo", error.message || "Milo could not respond right now.");
    } finally {
      setSending(false);
      input?.focus();
    }
  }

  openButton?.addEventListener("click", () => {
    setMiloOpen(true);
  });

  closeButton?.addEventListener("click", () => {
    setMiloOpen(false);
  });

  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMiloMessage(input?.value || "");
  });

  answerForm?.addEventListener("submit", (event) => {
    if (event.submitter?.dataset.loading === "true") {
      event.preventDefault();
      return;
    }
    const action = event.submitter?.value;
    if (action !== "hint" && action !== "solution") {
      return;
    }
    event.preventDefault();
    sendMiloAction(action);
  });

  input?.addEventListener("input", () => {
    if (sendButton) {
      sendButton.disabled = sending || !input.value.trim();
    }
  });

  quickActions.forEach((button) => {
    button.addEventListener("click", () => {
      sendMiloMessage(button.dataset.miloQuick || "");
    });
  });

  restoreMessages();
  const shouldRestoreOpen = storedOpenState();
  const shouldAnimateRestore = shouldRestoreOpen
    && Boolean(storedOpenProblemKey())
    && storedOpenProblemKey() !== currentProblemStorageKey();
  setMiloOpen(shouldRestoreOpen, false, shouldAnimateRestore);
  updateNudgeVisibility();
  restorePracticeButtons();
  setSending(false);
}

initializeMiloChat();
