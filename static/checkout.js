document.addEventListener("DOMContentLoaded", () => {
    const payBtn = document.getElementById("razorpay");

    if (!payBtn) return;

    payBtn.addEventListener("click", async () => {
        const amountInput = document.getElementById("amount");
        const receiverInput = document.getElementById("receiver");

        const amount = amountInput ? amountInput.value : null;
        const receiver = receiverInput && receiverInput.value
            ? receiverInput.value
            : "Merchant";

        if (!amount || amount <= 0) {
            Swal.fire({
                icon: 'error',
                title: 'Invalid Amount',
                text: 'Please enter a valid amount to pay.',
                background: '#1a1a1a', // Dark mode matches your app
                color: '#fff'
            });
            return;
        }

        // 🟢 STEP 1: FAKE UPI PIN ENTRY
        const { value: pin } = await Swal.fire({
            title: 'Enter UPI PIN',
            text: `Paying ₹${amount} to ${receiver}`,
            input: 'password',
            inputPlaceholder: 'Enter 4-digit PIN',
            inputAttributes: {
                maxlength: 4,
                autocapitalize: 'off',
                autocorrect: 'off'
            },
            showCancelButton: true,
            confirmButtonText: 'Pay Securely',
            confirmButtonColor: '#28a745', // Green
            background: '#141820', // Your App's Dark Theme
            color: '#fff',
            customClass: {
                input: 'swal-input-dark' // We will style this below if needed
            }
        });

        if (pin) {
            // 🟢 STEP 2: FAKE BANK PROCESSING SPINNER
            let timerInterval;
            Swal.fire({
                title: 'Processing Payment...',
                html: 'Contacting Bank Server...',
                timer: 2000, // 2 Second Fake Delay
                timerProgressBar: true,
                background: '#141820',
                color: '#fff',
                didOpen: () => {
                    Swal.showLoading();
                }
            }).then((result) => {
                // 🟢 STEP 3: SUCCESS & SAVE TO DB
                if (result.dismiss === Swal.DismissReason.timer) {
                    
                    // Actually save the expense to your Cloud DB
                    fetch("/api/add_upi_expense", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            amount: amount,
                            description: `UPI to ${receiver}`, 
                            // We send a fake ID, the backend doesn't check it anyway
                            razorpay_payment_id: "pay_simulated_" + Date.now() 
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        // 🟢 STEP 4: SUCCESS POPUP
                        Swal.fire({
                            icon: 'success',
                            title: 'Payment Successful!',
                            text: `Transaction ID: TXN${Date.now()}`,
                            background: '#141820',
                            color: '#fff',
                            confirmButtonColor: '#2c7df0'
                        }).then(() => {
                            window.location.href = "/dashboard";
                        });
                    });
                }
            });
        }
    });
});