
export default function ContactManagement() {
    return (
        <div>
            <h1>Contact Management</h1>


            <div>
                <label>contact_name</label>
                <input
                    type="text"
                    placeholder="contact_name"
                />
            </div>

            <div>
                <label>contact_email</label>
                <input
                    type="text"
                    placeholder="contact_email"
                />
            </div>


            <button>
                Submit
            </button>
        </div>
    );
}
