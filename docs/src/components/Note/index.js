import React from 'react'
import { Alert } from 'antd'


/**
 * Note is a React component that renders an Alert box message
 *
 * @param {object} obj
 * @param {string} obj.type - Type of alert (success, info, warning, error)
 * @param {string} obj.title - Title for the alert
 * @param {string} obj.children - Alert message
 */
const Note = ({ type = 'info', title = '', children }) => {
    return (
        <Alert
            type={type}
            message={title}
            description={children}
        />
    )
}

export default Note